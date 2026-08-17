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
leaving behind — surface them plainly in the Step 6 report.

**Never commit or push on Tebello's behalf just because `/session-end` is
running.** Only act on explicit confirmation this turn. Surfacing is the
job; deciding is Tebello's.

📍 **Also check the live copy, not just this repo.** If this session did
work in `~/Pappa T/…`, that is a separate git repo — run the same check
there. O-P-C's `Pappa T/` folder is a historical consolidation snapshot;
a commit pushed to the live vault's own remote does **not** appear here
until O-P-C is re-merged. Say so explicitly if that re-merge is now
outstanding. Operations sub-projects are archived (deleted 2026-08-10) and
do not need checking.

## Step 1.5 — Can This Session's Work Be Found?

Committed and pushed is not the same as reachable. Work sitting on a feature
branch with no PR is invisible to every session that starts from `main` — and
nothing about that state looks wrong: the tree is clean, the commits are
pushed, and this close-out reads like a success.

This session is the only one that knows what it just built, and this is the
last moment anyone will look at that branch on purpose.

**Run this in every repo this session touched, not just this hub.** A cloud
session commonly has this hub plus `tlelosa-claude-config` and/or a project
repo checked out together — a session that pushes two of them and opens a PR
for one looks finished, and the repo it didn't return to is easy to forget.
Two real cases landed this way: a PR template and a `/retro` install each sat
stranded in a second repo for a day while the queue recorded both as done,
because the session that built them only ran this check where it happened to
end up. List every repo this session touched, then run this — and Step 6's
report — once per repo:

```bash
git rev-parse --abbrev-ref HEAD
git log --oneline origin/main..HEAD
```

If HEAD is not `main` and the second command returns commits, report it in
Step 6, once per repo checked:

> **Branch state:** N commit(s) on `<branch>` not reachable from `main`.
> Invisible to any session starting from `main` until merged or a PR is
> opened.

**Report a pass in one line too** — "all commits reachable from `main`" —
because silence and never-ran look identical.

📍 **Run it in the live sub-project too**, on the same reasoning as Step 1's
caveat and against that repo's own default branch — Pappa T vault is on
`main`. (Operations sub-projects are archived.)

**Run this per repo, not once per session — the general case beyond just
the 📍 live-sub-project caveat above.** If this session touched more than one
repo (this hub plus `tlelosa-claude-config`, or any other repo attached
during the session), repeat the check in **each** one, not just whichever is
currently checked out. Two commits landed 2026-08-09/10 (the PR template,
`/retro`) each got a PR in one repo and were left stranded with no PR in the
other, both recorded done in a `docs/todo.md` anyway — a session that
finishes *a* PR still looks finished from inside a single repo.

**Never open the PR, merge, or push** to resolve this. Same rule as Step 1:
`/session-end` reports what it is leaving behind; it does not act on Tebello's
behalf. Naming the branch is the whole job — a branch that has been named is
one somebody can find again.

Why this belongs here rather than only in `/continue`: a resuming session can
find stranded work, but only after it has already been stranded, and it has no
idea which branch mattered. This step costs one command and catches it at the
source.

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

> SHA-citation for Done entries is proposed but not yet live here — spec at
> `tlelosa-claude-config/docs/specs/2026-08-12-done-sha-citation.md` is
> BLOCKED by reviewer (defects: `git log` misses changed-file cases, needs
> a fresh-fetch guard per Hard Rule 10, needs a pending state for
> PR-merge lag). This file briefly shipped the pre-review version live
> (PR #19, 2026-08-12) — reverted once the block was found. Don't add the
> requirement here until that spec is revised and approved.

**Hub-and-spoke:** if the work happened inside a project that keeps its own
`docs/todo.md`, that file is authoritative for the detail — update it there
and keep this hub's entry to a one-line at-a-glance pointer, per `CLAUDE.md`.

## Step 2.5 — Promote or Park Recurring "Known Risks" (per /retro findings)

Items that appear in 3+ consecutive session-log entries under "Known risks"
have never been decided, never been dropped, and are simply re-typed at every
close-out, which reads like tracking and functions like forgetting.

```bash
# Identify recurring items in the last 10 Known risks lines:
grep "^**Known risks:**" docs/session-log.md | tail -10
```

**If any risk appears in 3+ consecutive entries:**
- **Option 1 — Promote to decision:** Move it to `docs/todo.md` as an open
  decision item (Open or Backlog section). Reword it as a clear decision to
  be made, not a risk to be lived with. Add it to this entry's
  `**Next task:**` block in Step 3 so the next `/continue` notices it.
- **Option 2 — Move to Parked:** If the item has research behind it or
  explicit acknowledgment it's deferred (e.g., "parked at Tebello's
  direction"), move it to the Parked section of `docs/todo.md` and reference
  that in the Known risks line. Stop re-typing it in every session.

**Do not just re-type it again.** Once an item has been re-typed 3+ times,
it needs a deliberate disposition, not repetition.

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

Covers **Gap 3** ("the `knowledge/` cache can silently go stale") from
`docs/specs/2026-08-05-command-center.md`, per the design in
`tlelosa-claude-config/docs/specs/2026-08-04-session-end-command.md` item 3.
Gap 1 of that spec is `/overwatch`; Gap 2 is the agent-roster bootstrap in
the config repo.

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

**Which case you're in depends on the surface — this hub runs on both, so
establish it rather than assuming.**

- **CCD desktop** — impossible, not merely unreliable; there is nothing to
  attempt. Confirmed 2026-08-06 on the command's first real run:
  `set_session_title` rejects the current session *and* `list_sessions`
  excludes it, so a session has no way to obtain its own ID. No call can be
  constructed, so there is no error to report.
- **Claude Code Remote / web** — reachable, and this is the surface most of
  this hub's cloud sessions actually run on. Confirmed 2026-08-10: the
  session ID appears verbatim in the session URL, `list_sessions` returns the
  **current** session as its first row rather than excluding it, and
  `get_session`/`set_session_title` accept that ID. Sessions titled `Cont-"…"`
  already exist in this account's list, which is proof it has worked here.
  The call may still be gated on a tool-permission approval — an ordinary
  failure, not an impossibility.

- **Title set** → report it.
- **Attempted and refused** (permission denied, tool error) → say what
  happened in Step 6. Don't relabel this `not available in this environment`;
  that claims something stronger than what occurred.
- **No way to identify this session at all** (the CCD desktop case) → report
  `not available in this environment` in Step 6 and move on. Expected, not a
  failure. Don't go hunting for the session ID in logs, config, or
  transcripts.

Check the session URL and one `list_sessions` call before settling on the
third. Until 2026-08-10 this step named the desktop case as "this hub's usual
surface" and told every session not to try — which was wrong on the surface
doing most of the work.

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
**Branch state:** [Step 1.5, per repo touched this session — <repo>: all commits reachable from main | <repo>: N commit(s) on <branch> not reachable from main]
**Recurring Known risks:** [none found | <item> promoted to decision | <item> moved to Parked]
**Logged:** [docs/todo.md updated | + session-log.md entry added | + knowledge/<topic>.md updated]
**Title set:** [Cont-"<title>" | attempted, refused — <reason> | not available in this environment]
**Open follow-ups:** [none | listed, each already reflected in docs/todo.md]
```

Keep it short — this is a close-out, not a second resume report. If Step 1
surfaced uncommitted or unpushed work (here or in a live sub-project), lead
with that instead of burying it at the bottom.
