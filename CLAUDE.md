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

**Hub-and-spoke:** any sub-project with its own `CLAUDE.md`/`AGENTS.md`
takes precedence over this file for work done inside that project's
folder. This file governs cross-project decisions and new work started at
root — not everything everywhere.

-----

## 📍 Live copies vs. this repo's snapshot

`Operations/` and `Pappa T/` **inside this repo** are a historical
consolidation snapshot (the 2026-08-03 subtree merges — committed git
history only). The live working copies are `Desktop/Operations/` and
`Desktop/Pappa T/`, and those are separate git repos with their own
remotes, holding the gitignored runtime state (databases, `.env` files,
generated output) that a subtree merge structurally cannot capture.

Editing a file in this repo's snapshot does **not** reach the running
project — it only creates a re-merge to do later. Read the snapshot freely;
do actual project work in the live `Desktop/` copy. This is why `docs/todo.md`
flags items with 📍, and why `/overwatch` is forbidden from reading the
snapshot folders even as a fallback.

| Live repo | Default branch | Remote |
|---|---|---|
| `Desktop/Pappa T/` — **one** repo covering every sub-project (TebelloReborn, ai-outreach-agency, IQ, MIMS App, Tenders…) | `main` | `tlelosa-web/pappa-t` |
| `Desktop/Operations/2. SOPS/` | **`master`** | `tlelosa-web/sops` |
| `Desktop/Operations/3. Nameplate & Test Sheet/` | `main` | `tlelosa-web/NamePlateTool` |
| `Desktop/Operations/7. DELIVERY NOTE/delivery-note-system/` | `master` | **none — local only** |
| this hub | `main` | `tlelosa-web/Claude-Code` |

`Desktop/Operations/` is not itself a repo — it's a folder containing
several. Table verified 2026-08-10; per `knowledge/operations-hub.md` a
cached path table is a claim with an expiry date nothing in its own text
reveals, so re-check it rather than trust it.

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
data here with no second copy. Exit `2` or `3` means an invariant broke
(data/secret separation, or an excluded vault reaching the discovery set),
not an ordinary failure. `Desktop/Operations` is excluded **deliberately**
(Fan Movement contract terminated 2026-08-03) — don't add it back to "fix"
a Pappa-T-only backup.

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
   `docs/session-log.md`, and `knowledge/INDEX.md` get written by nearly
   every hub-level session — with Operations, Pappa T, and cloud sessions
   all able to run concurrently, stale-base edits to these three files have
   already caused two real merge conflicts (see `docs/session-log.md`,
   2026-07-28 entries). Before editing any of them, `git fetch origin` +
   `git pull origin main` (or merge/rebase onto latest `main`) first. If a
   conflict still happens anyway, resolve it as a real union of both
   sides' changes — never pick one branch and discard the other's work.
7. **Windows shell traps that have already cost this repo real time** —
   full detail in `knowledge/session-tooling.md`. The three that recur:
   `git commit -m` with a PowerShell here-string splits into pathspecs (use
   `-F <file>`); `Get-Content -Raw` decodes a BOM-less UTF-8 file as ANSI
   and silently mojibakes every em-dash, so round-trip source files through
   Python rather than PowerShell; and a `CHECKSUMS.txt` written by Python on
   Windows needs `newline=""` or `sha256sum -c` fails every line at once and
   reads like corrupt data.
