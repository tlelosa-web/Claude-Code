---
# /continue — Hub Session Resume
# Resumes work from where the last root-level session ended.
# Project-aware: identifies which project folder is in play before acting.
---

## Step 0 — Rename Stale Sessions

Before orienting, clean up titles left over from prior `/continue` runs:

1. Call `list_sessions` (this always excludes the current session, so it's
   safe to run — it can only surface *other* sessions).
2. For every other session still titled exactly `Continuation`, read its
   transcript with `list_events` (most recent 30 first; page backward with
   `before_uuid` if the actual task isn't visible yet) to find the concrete
   task it worked on — the first real user request after the `/continue`
   resume boilerplate, and what got built/fixed/decided.
3. Rename each one with `set_session_title` to `Cont-"<3-6 word
   context-based title>"` — describe what the session actually did, e.g.
   `Cont-"SOPS dashboard & BOM UI fixes batch"`, not the generic bootstrap
   exchange.
4. Skip a session if it has no real task yet (just the `/continue`
   resume-report exchange, no follow-up from Tebello) — leave it as
   `Continuation` until there's something to summarize.
5. **This session's own title is out of reach from inside itself** —
   `set_session_title` can only target other sessions. This session stays
   labeled `Continuation` until a *later* `/continue` run (in a different
   session) renames it per the steps above, or it's renamed manually.

If `list_sessions` (or `list_events`/`set_session_title`/`archive_session`
below) isn't available as a tool in this environment, say so plainly and
skip straight to Step 1 — don't treat a missing tool as an error to work
around. Confirmed missing in the Claude-Code-on-the-web cloud environment
as of 2026-07-28; may still be present on machines running the desktop/CLI
app with session-management enabled.

Then proceed to Step 0.5.

## Step 0.5 — Detect Superseded Sessions (ADR-005)

Check for sessions whose task has clearly been completed or made obsolete by
later work on the same project, and propose archiving them:

1. Group the `list_sessions` results (already fetched in Step 0) by `cwd`
   (project folder).
2. For any project folder with more than one open session, read enough of
   each *older* session's transcript with `list_events` (and that project's
   own `docs/todo.md` if it has one) to judge — don't assume — whether its
   task is actually done, merged, or superseded by a later session's work.
   Sessions on genuinely separate, still-relevant tasks (e.g. different
   batches/features in the same project) are **not** candidates just
   because a newer session exists — verified against this hub's own
   session list, where `2. SOPS` routinely has several legitimately
   parallel sessions open at once.
3. For each session judged superseded, propose it to Tebello by name/title
   with a one-line reason (e.g. "`Cont-\"Batch 25 resume: Edit Item
   modals\"` — that PR merged in a later session, this one's task is done").
4. **Never call `archive_session` speculatively.** Only archive a session
   Tebello has explicitly confirmed in this turn, one at a time.
5. If nothing looks superseded, say so briefly and move on — this step
   should not turn into an interrogation when the session list is clean.

Then proceed to Step 1.

## Step 1 — Orient

Read:
- `docs/todo.md` → current hub task queue and priorities
- `docs/session-log.md` → last session summary (final entry only)

## Step 1.5 — Shared Core Update Check (ADR-007)

Check whether the shared `CORE.md` (DCOE architecture, sub-agent roster,
model routing, universal hard rules — see the read instruction near the top
of this hub's `CLAUDE.md`) has upstream changes not yet pulled on this
machine:

```
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config fetch --quiet
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config rev-list HEAD..origin/main --count
```

If the count is > 0, mention it in the Step 3 resume report: "Shared core
template has N new commit(s) upstream — run `/plugin marketplace update
tlelosa-claude-config` to pull them in." This is a signal only — never run
the update automatically, and don't let it block orienting or reporting.
If the marketplace clone doesn't exist on this machine at all, note that
plainly too rather than silently skipping the check.

## Step 1.75 — Sync Check (prevents contention-file conflicts)

`docs/todo.md`, `docs/session-log.md`, and `knowledge/INDEX.md` are edited
by nearly every hub-level session, and this hub can have Operations,
Pappa T, and cloud sessions running concurrently. Editing any of these
three from a stale local `main` has already caused two real merge
conflicts (see `docs/session-log.md`, 2026-07-28 entries) — this step
exists to stop a third.

```
git fetch origin main --quiet
git -C . rev-list HEAD..origin/main --count
```

If the count is > 0, `git pull origin main` before doing anything else in
this session (Step 0-1's reads above are safe either way; this just makes
sure any *edit* later in the session starts from a current base). If the
pull produces conflicts on the three contention files, resolve as a real
union per `CLAUDE.md` Hard Rule 6 — never pick one side and drop the
other's work.

## Step 2 — Identify Scope

Is the next task:
- **Hub-level** (cross-project, or new work at root) → this `CLAUDE.md`
  governs.
- **Inside a specific project folder** → check whether that folder has its
  own `CLAUDE.md`/`AGENTS.md`. If it does, read it — it takes precedence
  over this file for anything inside that folder. If it doesn't, this hub
  brain's Hard Rules still apply, but stack-specific conventions must be
  confirmed with Tebello (Domain agent territory) rather than assumed.

## Step 2.5 — Flag Machine-Bound Tasks

Before reporting, check whether the candidate next task(s) (the `todo.md`
"Next task" plus any other open items you're about to surface) actually
need local filesystem/machine access this session doesn't have — e.g. a
vault/folder survey on Pappa T or Operations from a cloud
Claude-Code-on-the-web session, or any task whose description says "on
Pappa T"/"on Operations"/similar when the current session's environment
isn't that machine.

- Compare the task's stated machine against this session's actual
  environment (cloud sandbox vs. a specific named machine — check
  `knowledge/pappa-t.md` / `knowledge/operations-hub.md` if unsure which
  machine a task means).
- If a candidate task is machine-bound and this session can't reach that
  machine, don't drop it from the list — still surface it, but mark it
  clearly (e.g. "⚠️ requires local access on Pappa T — can't run from this
  session") in both the Step 3 report and its `AskUserQuestion` option
  description, so Tebello isn't offered it as if it were runnable here.
- This is a labeling check only — don't skip the task, don't silently
  reorder the queue, and don't try to work around the access gap (e.g. by
  guessing at the other machine's folder structure) without Tebello asking
  for that explicitly.

Then proceed to Step 3.

## Step 3 — Report State

Tell Tebello:
1. **Last completed task** — from `session-log.md`
2. **Next pending task** — from `todo.md`, with which project (if any) it
   touches
3. **Spec status** — does a spec exist in `docs/specs/` (or the project's
   own `docs/specs/`) for the next task, if it's a build task?
4. **Known risks** — surface the OneDrive/git item from `CLAUDE.md` if
   still unresolved
5. **Blockers** — anything unresolved, pending decisions, or missing
   context

Format:

```
## Session Resume

**Scope:** [Hub-level | <project folder name>]
**Last completed:** [task name]
**Next task:** [task name from todo.md — if machine-bound and unreachable from this session, say so here: "⚠️ requires local access on <machine> — not runnable from this session"]
**Spec:** [exists at docs/specs/<name>.md | MISSING — must write spec before building | N/A]
**Known risks:** [none new | OneDrive/git fix still pending, see docs/todo.md]
**Blockers:** [none | description — include any machine-access gap from Step 2.5 here too]

Ready to proceed? Confirm and I'll start.
```

**Then always follow the prose block with a selectable list** via
`AskUserQuestion` (single question, single-select unless the items are
clearly independent) — do not leave Tebello to respond in free text only.
Build the option list from every open item surfaced in this step: the
`todo.md` "Next task," plus any other still-open items mentioned in the
report (cross-project backlog items, a session flagged as possibly
duplicating work, etc.). Each option is one concrete item with a short
description of what picking it means — for any item flagged machine-bound
in Step 2.5, lead the description with the same ⚠️ access-gap note so it's
clear before Tebello picks it, not after. This was requested twice
independently (2026-07-17, two separate sessions) — treat it as a standing
preference, not a one-off.

## Step 4 — Wait for Confirmation

Do not begin implementation. Do not open files outside of the reads above.
Wait for Tebello to confirm the task or redirect.

## Spec Gate Reminder

If the next task is a build task and no spec exists → surface this
immediately. Spec must be written and confirmed before any executor is
dispatched.
