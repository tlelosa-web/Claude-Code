---
description: Review this hub's session log and queue for recurring framework friction, and propose a confirmable batch of fixes
---

# /retro — Hub Framework Retrospective

Hub instance of `hub-template/retro.md` (promoted per ADR-008, authorised by
`tlelosa-claude-config/docs/specs/2026-08-08-branch-triage-verdicts.md`,
Branch 3 LAND items 1–2). Beyond the shared skeleton, this instance names
this hub's actual paths, its four contention files, and its promotion path
into `tlelosa-claude-config`.

**Run this periodically — weekly, or whenever a session felt like a repeat of
one already done. Not every session.** It is the backward-looking counterpart
to `/continue`, not part of the routine.

> **Known gap:** on at least one session surface — a "Default"-type session in
> the Claude Code mobile app — typing a slash command returns "isn't available
> in this environment" even with a correctly formed command file, while the
> same file works via the `Skill` tool in a Claude Code Remote/web session
> (confirmed 2026-07-19, still unresolved; whether the desktop CLI is affected
> is tracked as an open item in `tlelosa-claude-config/docs/todo.md`).
> **Workaround:** ask in plain text ("run retro") instead of the slash form.

## Purpose

`/continue` orients on *what's next*. `/retro` asks a different question: did
this hub's own framework — `docs/todo.md` discipline, session-log hygiene,
`/continue`'s Step 0.5 dedup and Step 1.8/1.9 checks, `CLAUDE.md`'s Hard
Rules, `CORE.md`'s universal ones — actually hold up across recent sessions,
or did Tebello have to catch something the framework should have caught?

This is deliberately **not** a quality audit. A one-off mistake or a genuinely
new problem is out of scope. The target is the framework failing to prevent
repeat work.

## Step 1 — Gather evidence

Read, bounded to entries since the last `/retro` run (see Step 5):

- `docs/session-log.md` — every entry since the last retro marker.
  **This file's convention is "most recent last"** — the newest entries are at
  the tail, not the head. `grep -n "^## " docs/session-log.md | tail -20`
  gives the entry index cheaply; the file is thousands of lines and reading it
  whole is rarely the right move.
- `docs/todo.md` — current state, plus how long each item has sat unresolved.
  The "Parked (committed work, deliberately deferred)" and "Backlog / ideas
  (not committed)" sections matter here: a deliberately parked item is not
  friction, a silently deferred one is.
- `docs/decisions/` — ADR titles only, to check whether a friction point
  already has a fix proposed there but not yet executed.

If `docs/retro-log.md` doesn't exist yet, this is the first run — review the
full `session-log.md` history instead of a bounded window, and say so in the
report.

📍 **Hub-and-spoke applies.** Friction inside a sub-project that keeps its own
`docs/todo.md` belongs to that project's own retrospective. Only surface it
here if the *hub's* framework is what failed — e.g. the hub's queue carried a
stale claim about that project's state.

## Step 2 — Detect friction patterns

Look specifically for signals of the framework failing to hold state:

- A session re-did or re-proposed something a prior session already finished
  (redundant work)
- Tebello had to manually point out something already decided or completed,
  rather than the session catching it itself
- A session asserted a fact about external state (a git remote, a deployed
  version, another session's status, another repo's contents) that turned out
  to be stale or wrong — `CORE.md` hard rule 10 exists because of this class
- The same category of bug or gap recurs across 2+ session-log entries
- A `docs/todo.md` item has been deferred 3+ times without being dropped or
  actually scheduled
- A Done entry turned out to be false, half-true, or true only later — the
  queue asserting completion it didn't have is the same failure as a stale
  external-state claim, pointed inward

## Step 3 — Propose a batch

For each pattern found, write one proposal in this shape:

```
**Problem:** [one line, cite the session-log entry / todo item as evidence]
**Utility:** [new CORE.md hard rule | new skill | new hook | new
              CLAUDE.md/checklist item | new agent instruction]
**Scope:** [this hub only | universal — promote to tlelosa-claude-config so
            it reaches every machine/project]
**Effort:** [S | M | L]
```

Cap the batch at ~8 items. If more than 8 patterns surface, keep the
highest-evidence ones (cited by multiple entries) and note the rest were held
back rather than silently dropping them.

## Step 4 — Confirm before building anything

Present the batch, then **always follow it with a selectable list** via
`AskUserQuestion` (multiSelect — these are independent proposals; Tebello may
want some now and some later, or none). Never build a proposal that wasn't
picked.

Selected items become normal DCOE work from here:

- **Hub-only** fixes go straight to `docs/todo.md` as tasks, or to
  `docs/specs/` first if non-trivial.
- **Universal** items follow the existing promotion path (ADR-008) — fixed and
  proven here first, then migrated into `tlelosa-claude-config`:
  `dcoe-roster/CORE.md` for a hard rule, `shared-skills/` for a skill,
  `hub-template/` for a session-mechanics change. Both machines then pick it
  up via `/plugin marketplace update tlelosa-claude-config`. Note
  `hub-template/` is **copy-source, not a plugin** — a change there reaches
  this hub only when someone copies it in, which is the gap
  `HUB-CHECKLIST.md`'s diff-don't-assume rule exists to catch.

## Step 5 — Record the run

**Pull first.** `docs/retro-log.md` is this hub's **fourth contention file**,
alongside `docs/todo.md`, `docs/session-log.md`, and `knowledge/INDEX.md` —
see `CLAUDE.md` Hard Rule 6 and `/continue`'s Step 1.75. Operations, Pappa T,
and cloud sessions all write these concurrently, and stale-base edits to them
have already caused two real merge conflicts here. `git fetch origin` +
`git pull origin main` immediately before the append, not once at the start of
the run.

Then append to `docs/retro-log.md` (create it if missing):

```
## [date] — /retro run
Reviewed: session-log entries [range] | todo.md as of [date]
Proposed: N items — [M] selected, [N-M] deferred
Selected: [short list]
```

This is what bounds Step 1's next run to *new* entries only. Without it,
`/retro` would eventually repeat its own complaint — re-surfacing a pattern it
already raised and Tebello already declined to act on.

If a conflict happens on the append anyway, resolve it as a real **union** of
both sides — never keep one run's entry and discard the other's.
