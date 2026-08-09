# ADR-010 — Add `/session-end`, promoted the same way as `/continue` (ADR-008)

**Date:** 2026-08-05 (design decided 2026-08-04; the `Claude-Code` hub instance this ADR
records was not actually implemented until 2026-08-05 — see Correction below)
**Status:** Accepted — implemented in `tlelosa-claude-config` (`hub-template/`,
`.claude/commands/session-end.md`) and in this hub (`.claude/commands/session-end.md`)
**Owner:** Tebello Lelosa

## Correction (2026-08-05)

`tlelosa-claude-config/docs/todo.md`'s 2026-08-04 entry for this work claimed this ADR and
this hub's `session-end.md` instance already existed. Neither did — verified against the
filesystem during the Reviewer Loop for `docs/specs/2026-08-05-command-center.md`'s Gap 3
("knowledge cache can go stale"), which caught the false premise before it could ship on top
of a nonexistent file. This ADR is the actual, first-time record of that decision; the hub
instance it documents was built the same day this ADR was written, not the day before.

## Context

`/continue` orients a *new* session against whatever state the *last* one left behind — but
nothing on the other end of that handoff does the leaving-behind deliberately. A session just
stops: `docs/todo.md` may or may not be updated, `docs/session-log.md` (hub roots only) may or
may not get an entry, and the session's own title stays whatever generic default it started
with. `/continue`'s Step 0/0.5 (ADR-005) then has to reverse-engineer all of that from raw
transcripts on the next run — exactly the kind of re-derivation this hub's own knowledge-cache
discipline (`CLAUDE.md` Hard Rule 1) says to avoid.

Separately, this hub's knowledge cache (`knowledge/*.md`) has no enforcement at all beyond
prose ("update before ending a task that surfaced a reusable fact") — nothing prompts a
session to actually do it. `docs/specs/2026-08-05-command-center.md` ("Gap 3") identified this
as one of three command-center gaps and proposed folding a checklist prompt into
`/session-end` rather than building separate enforcement — the same command this ADR already
covers is the natural place for that prompt to live.

## Decision

Add a `/session-end` command, following the exact promotion pattern ADR-008 already
established for `/continue`:

1. **`tlelosa-claude-config/hub-template/session-end.md`** — a vault-agnostic skeleton: verify
   the working tree is clean (or surface what isn't), reconcile `docs/todo.md` (Done/Open),
   append a `docs/session-log.md` entry *if the vault keeps one*, prompt explicitly for a
   reusable-fact knowledge-cache update *if the vault keeps a `knowledge/` cache* (added
   2026-08-05, Gap 3), set this session's own title via `set_session_title` if that tool
   exists, and report a short close-out. No vault-specific content, so it can be copied
   verbatim into any hub root's `.claude/commands/session-end.md`, same as
   `hub-template/continue.md`.
2. **`tlelosa-claude-config/.claude/commands/session-end.md`** — minimal instance for this
   repo itself: no `session-log.md` (this repo keeps none, same reason `continue.md`'s local
   copy omits it), no `knowledge/` step (that cache lives in the `Claude-Code` hub, not here).
   Just `docs/todo.md` reconciliation + git-state check + title-set.
3. **`Claude-Code/.claude/commands/session-end.md`** — full hub instance: adds the
   `knowledge/<topic>.md` + `knowledge/INDEX.md` update step (Hard Rule 5 in this hub's own
   `CLAUDE.md`), including the explicit reusable-fact checklist question, and writes the
   `docs/session-log.md` entry in the existing dated-entry format (matches what `/continue`'s
   Step 1 already reads).

**Why a title-set, not a direct `archive_session` call:** `/continue`'s own Step 0 documents
that a session cannot rename or archive *itself* — `set_session_title`/`archive_session` only
ever target *other* sessions from within a given session's tool surface. So `/session-end`
cannot literally archive the session it's running in. What it can do is leave the session in a
state a **later** `/continue` run's Step 0/0.5 can recognize and archive immediately — by
setting the descriptive `Cont-"<title>"` title itself and making sure `docs/todo.md`/
`session-log.md` already reflect the work. That is what "prepare the session for archiving"
means here — the actual archive action stays a different session's/Tebello's call.

**Distribution mechanism:** file copy, same as `/continue` (ADR-008) — not a plugin/`@import`,
since this needs to run as each vault's own local slash command.

## Alternatives considered

- **Have `/session-end` call `archive_session` on itself** — not possible; ruled out by the
  tool-surface constraint documented in `/continue` Step 0 point 5, not a design preference.
- **Fold this into `/continue` itself** — rejected: `/continue` runs at session *start*; a
  close-out step belongs at the point work actually stops, which isn't a fixed offset from
  when it started. Keeping them separate also lets `/session-end` run mid-session as a
  checkpoint.
- **No shared template, author each vault's `session-end.md` independently** — rejected for
  the same reason ADR-008 rejected it for `/continue`: every fix would need independent
  rediscovery per vault instead of one shared skeleton.
- **A hard gate blocking session end until `knowledge/` is touched** (considered for the Gap 3
  addition specifically) — rejected: most sessions don't surface a new reusable fact, so a
  mandatory gate would be a false positive most of the time; a checklist prompt at the point
  the session is already reviewing itself is enough.

## Consequences

- `/continue`'s Step 0 gets cheaper over time as more sessions actually run `/session-end`
  before stopping — titles arrive pre-set instead of needing a transcript read, and
  `docs/todo.md`/`session-log.md` arrive already reconciled instead of stale.
- Like `/continue`, this is file-copy distribution — an improvement made to one vault's
  `session-end.md` doesn't propagate automatically to the others; backporting into
  `hub-template/session-end.md` and re-copying is a manual, deliberate step.
- The knowledge-cache checklist question (Gap 3) is soft, self-monitored enforcement, not a
  gate — it makes the existing Hard Rule 5 obligation harder to silently forget, not
  impossible to skip.
- This ADR's own history is itself an example of why the Reviewer Loop matters: a stale
  `docs/todo.md` claim asserted this ADR existed a day before it actually did, and that false
  claim would have propagated further (a "full instance" built to satisfy a citation that
  didn't exist) if the reviewer hadn't verified against the filesystem rather than trusting
  the todo entry.

## References

- `hub-template/session-end.md`, `tlelosa-claude-config/.claude/commands/session-end.md`,
  `Claude-Code/.claude/commands/session-end.md`
- ADR-008 (`ADR-008-hub-template-promotion.md`) — the `/continue` promotion this ADR mirrors
- `hub-template/continue.md` Step 0 / Step 0.5 (ADR-005) — the archive-detection flow this
  command feeds into
- `docs/specs/2026-08-05-command-center.md` (Gap 3) — the knowledge-freshness checklist
  addition folded into this command
