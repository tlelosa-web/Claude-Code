---
description: Consolidated read-only status view across this hub, every tracked sub-project, and the config repo
---

# /overwatch — Command Center Status View

Read-only aggregation, same spirit as the `reviewer` agent's read-only
contract. **Never writes, edits, or commits anything** — this command only
reads files and reports.

Covers **Gap 1** ("no single status view") from
`docs/specs/2026-08-05-command-center.md`. **Gap 2** (agent-roster bootstrap
check) and **Gap 3** (knowledge-freshness session-end prompt) are separate,
later Executor tasks per that spec's locked build order — not part of this
command.

Surfaces open items only. It never reads `docs/session-log.md` — recent
activity stays a separate, already-existing read if ever needed.

## Step 1 — This hub's own open items

Read `docs/todo.md` (this repo's root). Collect open items from its
**In progress**, **Next up**, and **Backlog / ideas** sections. Skip
**Done**.

## Step 2 — Each tracked sub-project

The project → path list below is **explicit and hand-maintained inside this
file** — deliberately not derived from `knowledge/INDEX.md` (that file has
no path column, and several of its rows are machine-level notes, not
individual projects — see the spec's Gap 1 correction). Update this list by
hand whenever a project repo is added or removed; there is no automatic
source for it.

All paths below are the **live** per-machine working copies. The hub's own
`docs/todo.md` explicitly flags O-P-C's `Operations/` and `Pappa T/` snapshot
folders as historical; `/overwatch` must never read them, even as a fallback.

> **Path verification as of 2026-08-12:** Operations folder and all its
> sub-projects (SOPS, NamePlateTool, delivery-note-system, daily-sales-order-files)
> were **deleted to the Recycle Bin on 2026-08-10** and are not being restored.
> `Desktop/Operations/` no longer exists. The Fan Movement contract terminated
> 2026-08-03; project data is archived in the Fan Movement staged copy only.
> See `CLAUDE.md`'s "Live copies vs. this repo's snapshot" section.

**⚠️ Operations — ARCHIVED (not monitored):**

Operations projects are no longer live on this machine. Their state is
preserved in:
- This repo's `Operations/` snapshot folder (git history only, no runtime state)
- The Fan Movement staged copy (`Desktop/Fan Movement - Company IP/`, if present)
- GitHub private repos (`tlelosa-web/sops`, `tlelosa-web/NamePlateTool`)

`/overwatch` does **not** attempt to read these — they are archived and the
deletion is deliberate. If a project needs to be reactivated, restore from the
GitHub remote or the Fan Movement handover folder.

**Pappa T sub-projects:**

| Project | `docs/todo.md` path |
|---|---|
| TebelloReborn | `~/Pappa T/TebelloReborn/docs/todo.md` |
| ai-outreach-agency | `~/Pappa T/ai-outreach-agency/docs/todo.md` — verified present 2026-08-09 |

**No `docs/todo.md` — verified absent 2026-08-09, not merely unconfirmed:**
MIMS App, IQ Signal Generator, and Tenders all use a different scaffold from the
rest of this vault, none of their `knowledge/*.md` files cite a `docs/todo.md`
as an actual source, and none has one on disk:

| Project | Live folder | Brain/status file actually cited |
|---|---|---|
| MIMS App | `~/Pappa T/MIMS App/` | `GEMINI.md` (Gemini-driven, not DCOE — "Directive → Orchestration → Execution" structure, per `knowledge/mims-app.md`) |
| IQ Signal Generator | `~/Pappa T/IQ/` | `1_Documentation/AGENT.md` (generic "MASTER AGENT DIRECTIVE" boilerplate, per `knowledge/iq-signal-generator.md`) |
| Tenders | `~/Pappa T/Tenders/` | `1_Documentation/AGENT.md` (same boilerplate as IQ; the only `docs/todo.md` `knowledge/tenders-sa.md` cites is the **hub's own** `docs/todo.md` tracking a submodule fix, not a project-level file, per `knowledge/tenders-sa.md`) |

For these three, do not attempt to read a `docs/todo.md` at all — the point is
not that one might exist unfound, but that these projects genuinely don't use
the convention. Use the same handling as daily-sales-order-files: print
"no confirmed `docs/todo.md` convention — status per last known knowledge-cache
entry" for each, and never invent a path to probe.

**Deliberately excluded from this list:** `cratetracker`
(`tlelosa-web/cratetracker`) — a standalone public GitHub repo whose
`docs/todo.md`/DCOE-tracking status has never been verified. `pitwall-companion`
(`tlelosa-web/pitwall-companion`) is also excluded, but for a *confirmed* reason,
not an unverified one — this hub's own `docs/todo.md` (2026-07-31 entry) and
`docs/session-log.md` both state directly that it "has no `docs/todo.md` of its
own." Neither omission is an oversight — don't add either without first
verifying (or, for pitwall-companion, without that fact having changed).

For each project across all three tables above, attempt to read its
`docs/todo.md`:

- **Reachable, has open items** — list them (title + one-line status),
  tagged with the project name.
- **Reachable, zero open items** — say so briefly: "no open items."
- **Path not reachable from this session/environment** (e.g. a
  `Desktop/...` or `C:\Dev\...` path from a cloud session with no access to
  that machine) — print a one-line "⚠️ unreachable from this environment"
  note for that project. Do not fail the whole command over one
  unreachable project.
- **daily-sales-order-files, MIMS App, IQ Signal Generator, Tenders
  specifically** — none of these four have a confirmed `docs/todo.md`
  convention (see the "Unconfirmed `docs/todo.md` convention" table above).
  Do not attempt to read a file that isn't confirmed to exist. Instead print:
  "no confirmed `docs/todo.md` convention — status per last known
  knowledge-cache entry."

## Step 3 — Config repo's own open items

Read `~/.claude/plugins/marketplaces/tlelosa-claude-config/docs/todo.md`.
Collect its Open items the same way as Step 1. This repo is tracked
separately from Step 2's project list — it's the config/marketplace repo,
not a sub-project under Operations or Pappa T.

**The path is exact on purpose, and the sibling path this step used to name
(`../tlelosa-claude-config/`) does not exist.** There are two clones of this
repo on this machine: the marketplace clone above, which is the one
`/continue` Step 1.5 reads and the one that governs, and a stray
`~/Downloads/tlelosa-claude-config` noted in `knowledge/pappa-t.md`. On
2026-08-08 a fix was applied to the wrong one and reported as done while the
governing clone stayed broken. Always path-qualify with `git -C`, and never
resolve this repo by looking around for it.

## Step 4 — Render the consolidated report

Plain text, in-session. **No Artifact, no file writes** — this command
never edits anything, and an Artifact dashboard is explicitly out of scope
here (a possible later, separate skill per the spec, not part of this
command).

Group output by project. Use the 📍/⚠️ flag convention already used in this
hub's own `docs/todo.md` where it fits naturally: 📍 for "reachable from
this machine, but note the live-vs-snapshot path distinction" style flags,
⚠️ for "can't reach this from the current environment." Lead with a
top-line summary count.

Format:

```
## Overwatch — Status Across All Tracked Projects

**Summary:** X open item(s) across Y project(s) (Z unreachable this run)

### This hub (Claude-Code)
- [item] — [status]
- ...  (or "no open items")

### Operations (ARCHIVED)
All Operations sub-projects were deleted 2026-08-10 and are not monitored.
Data preserved in: O-P-C snapshot, Fan Movement handover folder, GitHub remotes.

### Pappa T
**TebelloReborn**
- [item] — [status]
  (or: ⚠️ unreachable from this environment)

**ai-outreach-agency**
- ...

**MIMS App**
- no confirmed docs/todo.md convention — status per last known knowledge-cache entry

**IQ Signal Generator**
- no confirmed docs/todo.md convention — status per last known knowledge-cache entry

**Tenders**
- no confirmed docs/todo.md convention — status per last known knowledge-cache entry

### tlelosa-claude-config
- [item] — [status]  (or "no open items")

**Excluded from this list:** cratetracker (convention never verified),
pitwall-companion (confirmed to have no docs/todo.md, per this hub's own
docs/todo.md/session-log.md). See overwatch.md for why.
```

This command does not offer an `AskUserQuestion` follow-up and does not ask
for confirmation to proceed — it's a read-only report, not a task handoff.
Once rendered, stop.
