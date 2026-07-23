# CLAUDE.md — Claude-Code

# Owner: Tebello Lelosa

> A knowledge cache, not an app. Purpose: don't re-derive facts already
> found in a prior session. Read `knowledge/INDEX.md` at session start.

-----

## How this repo works

This is a flat, topic-keyed lookup cache — not a task tracker, not a hub
with its own session machinery (see `tlelosa-claude-config`'s
`hub-template/` for that pattern; this is a narrower tool). Two rules:

1. **Before researching anything** not already in this session's context,
   check `knowledge/INDEX.md` for a matching topic. If found, read that
   file instead of re-deriving the answer.
2. **Before ending a task** that surfaced a reusable fact (a config quirk,
   a decision, an API behavior, an approach that didn't work) — append it
   to the matching `knowledge/<topic>.md` (create a new one if nothing
   fits), and update its line in `knowledge/INDEX.md`.

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

1. Keep entries factual and usable as-is — not a transcript summary, the
   actual data/decision/gotcha.
2. Superseded entries are marked `Status: superseded`, not deleted — the
   history of what changed is itself useful context.
3. One topic = one file. Split a file once it's covering more than one
   clearly separate subject.
4. No company or project data beyond what's already public in the source
   project's own repo — same discipline as `tlelosa-claude-config`.
