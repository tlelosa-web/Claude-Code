# ADR-005 — Context budget threshold + judgment-based session archival

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

Tebello asked for two productivity mechanisms:

1. A context-monitoring rule so a session doesn't keep working once its
   remaining context budget gets too low to reason reliably.
2. Session tracking so that when a session on a given project is superseded
   by a later one, the earlier one gets archived instead of sitting open
   indefinitely.

Investigation before implementing surfaced two constraints that shaped the
decision:

- **No harness hook reads live context percentage.** Claude Code hooks fire
  on tool/lifecycle events, not on token-budget state. There is no
  mechanism to have the harness itself force a stop at a percentage
  threshold. The only lever available is a written policy the agent
  follows by reading `CLAUDE.md` each session — self-monitored, not
  harness-enforced.
- **`archive_session` always requires per-call user confirmation** — it
  explicitly refuses speculative/automatic use. A live check of open
  sessions also showed `2. SOPS` alone has 5 concurrent sessions (Batch 25,
  Batch 26, Payment status, Stocked finished good, Batch rename) that are
  parallel work, not duplicates. A mechanical "newest session on this
  folder wins" rule would have wrongly flagged 4 of those 5. Archival
  therefore has to be judgment-based (read the session's actual task before
  proposing it) and always ends in an explicit per-session confirmation,
  never a silent batch action.

Tebello confirmed both directions via the recommended options: self-monitoring
CLAUDE.md policy for the context rule, and judgment-based (not mechanical)
detection for archival candidates.

## Decision

1. **Context budget rule (`CLAUDE.md` § Context Management):** raise the
   existing informal "~50%" note to a firm rule — at ~45% context consumed
   (55% remaining), stop starting new implementation work, write current
   state to `docs/session-log.md` and `docs/todo.md`, and prompt Tebello to
   `/compact` or start a fresh session. This replaces the old soft
   suggestion with a specific threshold and a defined handoff action.
2. **Session-archival check added to `.claude/commands/continue.md`** as a
   new step between the existing "rename stale sessions" step and
   "orient": for sessions sharing a project's cwd, read enough of each
   transcript (and the project's own `docs/todo.md` if present) to judge
   whether an older session's task is actually done or made obsolete by a
   newer one. Only sessions judged superseded get proposed to Tebello for
   archiving, one at a time — `archive_session` is never called without
   that per-item confirmation in the same turn.
3. **Both patterns recorded in `docs/patterns.md`** as hub-native (not
   promoted from a sub-project, since session management is a hub-level/
   harness-level concern) so they're visible as reusable technique if a
   sub-project ever wants its own `/continue` to do the same.

## Consequences

- No change to harness/settings.json — this is a documentation/prompt-level
  change, not a hooks or permissions change.
- The context rule only works if the agent actually reads and follows
  `CLAUDE.md` each session — same trust model as every other rule in this
  file (Hard Rules, spec gate, etc.), not a new category of risk.
- Archival remains a two-step flow (propose → confirm) by design, matching
  the tool's own constraint. Nothing in this ADR makes archiving fully
  automatic, and none should be built later without revisiting this ADR.
- Sub-project `CLAUDE.md`s are unaffected — this governs root-level session
  behavior only, per the hub-and-spoke rule (sub-projects govern themselves
  inside their own folders).
