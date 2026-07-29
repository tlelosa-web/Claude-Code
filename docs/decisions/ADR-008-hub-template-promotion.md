# ADR-008 — Promote the hub-and-spoke `/continue` pattern to a shared, vault-agnostic template

**Date:** 2026-07-21 (approximate — dated to the `hub-template/` addition in
`tlelosa-claude-config`; exact commit date not independently re-verified
this session)
**Status:** Accepted — implemented in `tlelosa-claude-config` (`hub-template/`)
**Owner:** Tebello Lelosa

## Context

The Operations hub (this repo, `Claude-Code`) piloted a hub-and-spoke
session-resume pattern: a root `CLAUDE.md` describing project scope and
hard rules, a `docs/todo.md` + `docs/session-log.md` pair as the actual
task queue and log, and a `.claude/commands/continue.md` slash command
that orients a fresh session against that state before starting work.

Once this proved out on Operations, the same shape was needed at other
Tebello-governed vault roots (Pappa T's own hub, this `tlelosa-claude-config`
repo's own lightweight `/continue`) — but `continue.md` as written for
Operations carried Operations-specific content (session-hygiene tool
names, that hub's own project index references), so it couldn't be copied
verbatim to a different vault without editing out what didn't apply.

## Decision

Extract the mechanical skeleton of the hub-and-spoke pattern into
`tlelosa-claude-config/hub-template/`, following the same "promote what's
proven, don't duplicate it" principle already used for the DCOE roster
(`dcoe-roster/CORE.md`, ADR-007):

1. **`hub-template/continue.md`** — a vault-agnostic version of the
   `/continue` resume flow: read the vault's own `docs/todo.md` +
   `docs/session-log.md`, report state, wait for confirmation. Contains no
   Operations-specific content, so it can be copied into any hub root's
   `.claude/commands/continue.md` verbatim.
2. **`hub-template/HUB-CHECKLIST.md`** — not a file to install as-is, but
   a checklist a session reconciles a hub root's own `CLAUDE.md` against:
   CORE.md read instruction present, `continue.md` actually exists on
   disk (not just described in prose), hard rules don't relax `CORE.md`'s
   universal ones, hub-and-spoke precedence is stated explicitly,
   `docs/todo.md`/`docs/session-log.md` exist and are what `continue.md`
   actually reads, and the note-frontmatter convention is documented. A
   hub root's real content (project index, life-domain sections) is never
   overwritten by this checklist — only the minimum scaffolding items are
   added or flagged.
3. **Distribution mechanism:** file copy, not a plugin or `@import`. Unlike
   `CORE.md` (ADR-007), the hub template isn't read live at every session
   start — it's a one-time (or occasional-update) copy into each vault's
   own `.claude/commands/continue.md`, since the resume flow needs to run
   as that vault's own command, not a shared plugin command.
4. **Verification step baked into the checklist:** after reconciling a
   hub root's `CLAUDE.md` against the checklist, open a fresh session at
   that root and run `/continue` — a working result is a real resume
   report grounded in that vault's own `docs/todo.md`/session-log, not
   silence, a "command not found" error, or another vault's project data
   leaking in (the last case meaning the file landed in the wrong place,
   not that the mechanism itself is broken).

## Alternatives considered

- **Copy the Operations `continue.md` as-is to each new vault, editing out
  Operations-specific content each time** — rejected: same drift problem
  the `CORE.md` distribution (ADR-007) was designed to avoid; every copy
  is a fork that can silently diverge from process improvements made
  elsewhere.
- **A single shared `/continue` command distributed like `CORE.md`
  (plugin + read instruction)** — rejected: the resume flow needs to be
  each vault's own command (invoked as `/continue` locally, reading that
  vault's own task files), not a shared file read into context — a plugin
  command distribution model doesn't fit a per-vault slash command the
  way it fits a shared knowledge file.
- **Leave each vault's `/continue` independently authored, no shared
  skeleton** — rejected: this repo's own `Step 0.5` (session-archival
  rule) and `Step 1.5`/`Step 1.75` (shared-core update check, sync check)
  improvements were process fixes worth propagating to every hub, not
  just this one; an unshared skeleton means every fix has to be
  independently rediscovered per vault.

## Consequences

- Any new Tebello-governed vault root can adopt the hub-and-spoke pattern
  by copying `hub-template/continue.md` in verbatim and running through
  `HUB-CHECKLIST.md`, instead of re-deriving the pattern from scratch or
  forking Operations' own copy.
- Process improvements discovered in any one hub's `continue.md` (e.g.
  this repo's Step 0.5 broadening, Step 1.75 sync check) are candidates to
  fold back into `hub-template/continue.md` so future vault adoptions
  start from the improved version — though existing hubs' own
  `continue.md` copies don't auto-update (file-copy distribution, not a
  live read per ADR-007's model), so backporting is a manual, deliberate
  step per hub.
- `HUB-CHECKLIST.md`'s "reconcile, don't overwrite" discipline protects
  each vault's genuinely local content (its own project index, its own
  life-domain sections) from being clobbered by template adoption.
- The same "promote what's proven" principle was applied a third time for
  Skills (`hub-template/SKILLS-AUDIT-CHECKLIST.md`), reusing this ADR and
  ADR-007 as precedent rather than re-justifying the pattern from
  scratch.

## References

- `hub-template/continue.md`, `hub-template/HUB-CHECKLIST.md`,
  `hub-template/SKILLS-AUDIT-CHECKLIST.md`
- `tlelosa-claude-config` README.md ("hub-template" section)
- This repo's own `.claude/commands/continue.md` — the Operations-hub
  instance this template was extracted from
- Related: ADR-007 (CORE.md distribution — same "promote what's proven"
  principle, different distribution mechanism since this is a per-vault
  command rather than a shared read-only file)
