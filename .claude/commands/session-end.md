---
description: Close out this hub session — reconcile the queue, log it, prep it for archiving
---

# /session-end — Hub Session Close-Out

Full hub adaptation of `hub-template/session-end.md` (promoted per ADR-008,
spec: `tlelosa-claude-config/docs/specs/2026-08-04-session-end-command.md`).
Runs when work stops — or mid-session as a checkpoint — so the *next*
`/continue` run reads deliberate state instead of reverse-engineering it
from a transcript.

Beyond the shared skeleton, this instance adds what only the hub needs: the
Hard Rule 6 pull-first gate, the `knowledge/` cache step (Hard Rule 5), the
`docs/session-log.md` dated-entry format `/continue` Step 1 reads, and the
live-Desktop-copy caveat from the O-P-C consolidation.

## Step 0 — Pull Before You Write (Hard Rule 6)

**Do this first, before touching anything.** This command writes to all
three of the hub's contention files — `docs/todo.md`, `docs/session-log.md`,
and `knowledge/INDEX.md` — which is exactly the pattern that has already
caused two real merge conflicts here.

```bash
git fetch origin main --quiet
git rev-list HEAD..origin/main --count
```

If the count is > 0, `git pull origin main` before writing anything. If a
conflict happens anyway, resolve it as a real **union** of both sides —
never pick one branch and discard the other's work.

## Step 1 — Check Working Tree State

```bash
git status --short --branch
git log --oneline -5
```

Uncommitted changes and unpushed commits are part of what this session is
leaving behind — surface them plainly in the Step 5 report.

**Never commit or push on Tebello's behalf just because `/session-end` is
running.** Only act on explicit confirmation this turn. Surfacing is the
job; deciding is Tebello's.

📍 **Also check the live copy, not just this repo.** If this session did
work in `Desktop/Operations/…` or `Desktop/Pappa T/…`, those are separate
git repos — run the same check there. O-P-C's `Operations/`/`Pappa T/`
folders are a historical consolidation snapshot; a commit pushed to a live
sub-project's own remote does **not** appear here until O-P-C is re-merged.
Say so explicitly if that re-merge is now outstanding.

## Step 2 — Reconcile the Task Queue

Open `docs/todo.md`:

- Move anything actually finished this session from Open → Done, with a
  one-line summary: what changed, and where the detail lives (spec file,
  commit, PR).
- Add any newly-discovered open item this session surfaced that isn't
  tracked yet. If it's a real commitment, it goes under "Next up"; if it's
  an idea Tebello hasn't agreed to, it goes under "Backlog / ideas (not
  committed)" — don't promote on your own.
- Leave items this session didn't touch alone. This step reconciles; it
  does not re-audit the backlog.

**Hub-and-spoke:** if the work happened inside a project that keeps its own
`docs/todo.md`, that file is authoritative for the detail — update it there
and keep this hub's entry to a one-line at-a-glance pointer, per `CLAUDE.md`.

## Step 3 — Write the Session-Log Entry

Append a new dated entry to `docs/session-log.md` in the existing format,
ending with the exact block `/continue` Step 1 expects to read:

```
**Last completed:** …
**Next task:** …
**Known risks:** …
**Blockers:** …
```

**Then verify the entry actually landed last:**

```bash
grep -n "^## " docs/session-log.md | tail -5
```

This file's convention is "most recent last," and `/continue` Step 1 reads
**only the final entry** — so an out-of-order entry silently serves stale
state to every later session. This is not hypothetical: on 2026-08-06 a
clean auto-merge from PR #14 landed the 2026-08-04 entry *above* two
2026-08-03 entries, and it took a commit-diff comparison to notice. Hard
Rule 6's pull-first gate prevents *conflicts*, not *misordering* — so check
the tail explicitly rather than trusting that an append went where you meant.

If a bare marker line sits directly above an entry (e.g. the
`codex-review …: ran` line the codex-gate skill writes), that adjacency can
be load-bearing — entries reference it as "one line above this entry."
Don't reorder across it.

## Step 4 — Update the Knowledge Cache (Hard Rule 5)

If this session surfaced a reusable fact — a config quirk, a decision, an
API behavior, an approach that didn't work — it belongs in `knowledge/`
now, not "later." The whole point of the cache is that the next session
doesn't re-derive it (Hard Rule 1).

- Append a dated entry to the matching `knowledge/<topic>.md`, most recent
  first, in the standard format (`## YYYY-MM-DD — <title>`, `**Source:**`,
  `**Status:** active | superseded`).
- One topic = one file — create a new file if nothing fits (Hard Rule 3).
- Superseding an old entry means marking it `Status: superseded`, **not**
  deleting it (Hard Rule 2).
- Update that file's row in `knowledge/INDEX.md`, including the
  last-updated date.

Write the finding itself — the actual data, decision, or gotcha — not a
summary of the conversation that produced it.

## Step 5 — Set This Session's Title

If `set_session_title` is available, set **this** session's title to
`Cont-"<3-6 word context-based title>"`, describing what the session
actually did — the same convention `/continue` Step 0 uses when renaming
other sessions.

Note that `/continue` Step 0 point 5 documents the opposite constraint —
that a session cannot rename *itself* — because on that tool surface
`set_session_title` targets only other sessions. Availability differs by
environment (desktop/CLI vs. cloud). So: attempt it, and if it fails or
isn't available, say so plainly and move on. Don't treat it as an error to
work around, and **never** call `archive_session` on this session.

Setting a good title *is* the "prep for archiving" — the actual archive
stays a later `/continue` run's or Tebello's call.

## Step 6 — Report Close-Out

```
## Session End

**Committed:** [what's committed this session, or "nothing to commit"]
**Pushed:** [clean — nothing outstanding | N unpushed commit(s) on <branch>]
**Logged:** [docs/todo.md updated | + session-log.md entry added | + knowledge/<topic>.md updated]
**Title set:** [Cont-"<title>" | not available in this environment]
**Open follow-ups:** [none | listed, each already reflected in docs/todo.md]
```

Keep it short — this is a close-out, not a second resume report. If Step 1
surfaced uncommitted or unpushed work (here or in a live sub-project), lead
with that instead of burying it at the bottom.
