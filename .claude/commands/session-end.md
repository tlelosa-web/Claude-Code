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

Make sure `docs/session-log.md` ends with a dated entry covering this
session, in the existing format, ending with the exact block `/continue`
Step 1 expects to read:

```
**Last completed:** …
**Next task:** …
**Known risks:** …
**Blockers:** …
```

**Reconcile — don't blindly append.** Check what's already there first:

- **Work not logged yet** → append a new entry. The common case.
- **Session already wrote its own entries** → don't restate them. Either add
  a short entry covering only what's new since (and say so explicitly, so it
  doesn't read as a duplicate), or verify the existing final entry's
  `Last completed:` / `Next task:` block is still accurate and leave it.
- **Second `/session-end` run in the same session** (mid-session checkpoint,
  then again at the end) → extend or replace the entry the first run wrote,
  rather than adding a near-empty second one.

An entry should be the session's *output*, not a record that a close-out
command ran.

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

**On this hub's usual surface (CCD desktop) this step is impossible, not
merely unreliable — there is nothing to attempt.** Confirmed 2026-08-06 on
the command's first real run: `set_session_title` rejects the current
session *and* `list_sessions` excludes it, so a session has no way to obtain
its own ID. No call can be constructed, so there is no error to report.

- **Self-titling reachable** → set the title.
- **No way to identify this session** (the case here) → report
  `not available in this environment` in Step 6 and move on. Expected, not a
  failure. Don't go hunting for the session ID in logs, config, or
  transcripts.

**Never** call `archive_session` on this session either way.

Setting a good title, *where possible*, is the "prep for archiving" — the
actual archive stays a later `/continue` run's or Tebello's call. Where it
isn't possible, Steps 2-4's reconciliation is what makes that later
judgment easy, which is most of the value regardless.

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
