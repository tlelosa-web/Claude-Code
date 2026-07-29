# ADR-007 — Distribute CORE.md via a read instruction, not `@import`

**Date:** 2026-07-18
**Status:** Accepted — implemented in `tlelosa-claude-config` (`dcoe-roster` plugin)
**Owner:** Tebello Lelosa

## Context

The DCOE architecture (Domain → Context → Orchestrate → Execute), the
9-agent sub-agent roster, model routing, and the universal hard rules
needed to be shared across every opted-in project on both machines
(Operations and Pappa T) from one canonical file, rather than copy-pasted
per project and drifting.

Claude Code's `CLAUDE.md` supports `@path` imports for pulling in other
files. The natural design was to have each project's `CLAUDE.md`
`@import` the shared core file directly. Confirmed 2026-07-18: Claude
Code's `@path` import mechanism does not resolve absolute paths outside
the importing project's own tree — a plugin-distributed file living at
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
is outside every project's tree by construction, so `@import` cannot reach
it.

## Decision

Distribute `CORE.md` via a plain **read instruction**, not `@import`:

1. `dcoe-roster/CORE.md` ships as part of the `dcoe-roster` marketplace
   plugin, installed at user scope so it lands at the same absolute path
   on every machine:
   `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`.
2. Any project that opts into the DCOE pattern carries a short instruction
   near the top of its own `CLAUDE.md` telling Claude to read that file at
   session start and treat its contents — architecture, roster table,
   model routing, universal hard rules — as part of that session's
   operating instructions, on the same footing as any other rule in the
   project's own `CLAUDE.md`.
3. If the path doesn't exist on a given machine (plugin not installed
   yet, or a machine without the marketplace configured), the project's
   own instruction says so explicitly rather than silently proceeding as
   if the shared core were loaded.
4. `CORE.md` itself documents this distribution mechanism at its own top,
   so anyone reading the file in isolation understands why it isn't wired
   in via `@import`.

## Alternatives considered

- **`@import` the plugin path directly** — rejected: doesn't work, by
  construction (confirmed above). Would silently fail to load the shared
  core with no visible error, which is worse than an explicit read
  instruction that at least states the dependency plainly.
- **Copy `CORE.md`'s content into each project's own `CLAUDE.md`** —
  rejected: reintroduces the drift problem this design exists to solve —
  N copies to keep in sync by hand instead of one canonical file plus a
  plugin update.
- **A build/sync script that writes `CORE.md`'s content into each
  project's `CLAUDE.md` at install time** — rejected as unnecessary
  complexity: a read instruction achieves the same effect without a
  script to maintain, and keeps the single source of truth genuinely
  singular (one file, read live, not stamped copies that go stale the
  moment `CORE.md` is next edited).

## Consequences

- Every opted-in project's `CLAUDE.md` carries one short, explicit
  dependency line instead of an invisible import that may or may not have
  worked.
- `CORE.md` updates propagate to every project the next time a session
  starts and re-reads it — no per-project sync step, as long as the
  `dcoe-roster` plugin itself has been updated on that machine
  (`/plugin marketplace update tlelosa-claude-config`).
- A machine or project that hasn't installed the plugin gets a visible
  "path doesn't exist" statement rather than a silent partial load — the
  same discipline this hub's own `CLAUDE.md` follows for reading
  `CORE.md` at session start.
- This same "shared file, read instruction, not `@import`" pattern was
  reused one level up for hub-to-hub distribution (`hub-template/`, see
  ADR-008) and for the `docs/decisions/` note-frontmatter convention in
  `hub-template/HUB-CHECKLIST.md`.

## References

- `dcoe-roster/CORE.md` (top-of-file distribution note)
- `tlelosa-claude-config` README.md ("dcoe-roster" section)
- `hub-template/HUB-CHECKLIST.md` (cites this ADR for the CORE.md
  read-instruction checklist item)
- Related: ADR-008 (hub-template promotion — same distribution pattern
  applied to `/continue`)
