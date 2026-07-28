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
