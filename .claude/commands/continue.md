---
description: Resume hub work from where the last root-level session ended
---

# /continue — Hub Session Resume

Resumes work from where the last root-level session ended. Project-aware:
identifies which project folder is in play before acting.

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

## Step 0.5 — Detect Superseded or Stale Sessions (ADR-005, broadened 2026-07-29)

Originally this step only caught sessions clearly superseded by later work
in the *same* project — a narrow bar that let plain-old-idle sessions pile
up unarchived even when nothing about them was ambiguous. It now checks
two independent categories each run; a session only needs to match one:

**A. Superseded** — task completed or made obsolete by later work on the
same project:

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

**B. Stale/idle** — nothing to do with whether the task is superseded,
just whether the session is plainly dead weight:

1. Using `list_sessions`' last-activity timestamp for each other session,
   flag any session with **no activity in 7+ days**.
2. For each flagged session, read enough of its transcript with
   `list_events` to sanity-check it's actually dead, not just quiet
   because it's mid-wait on something external (e.g. blocked on Tebello's
   go-ahead per a spec, waiting on IT, watching a PR). A session with a
   real open thread stays off the list even if it's old — staleness is
   about abandonment, not age alone.
3. Also flag single-exchange sessions with no follow-up task (the same
   condition Step 0 point 4 uses to skip renaming) once they're past the
   7-day mark — a `Continuation` session nobody ever gave a real task to
   is the clearest case of dead weight there is.
4. For each session flagged stale, propose it to Tebello by name/title
   with a one-line reason (e.g. "`Cont-\"Draft outreach copy edits\"` —
   last activity 2026-07-14, no open thread, nothing pending").

**Both categories:**

- **Never call `archive_session` speculatively.** Only archive a session
  Tebello has explicitly confirmed in this turn, one at a time.
- Present superseded and stale candidates together as one combined list so
  Tebello isn't asked twice in the same run.
- If nothing looks superseded or stale, say so briefly and move on — this
  step should not turn into an interrogation when the session list is
  clean.

Then proceed to Step 1.

## Step 1 — Orient

Read:
- `docs/todo.md` → current hub task queue and priorities
- `docs/session-log.md` → last session summary (final entry only)

Read both as a **claim with a timestamp**, not as state. Neither is
verified until Step 1.9 has compared them against the live sub-project
repos they name — do not carry anything from them into the Step 3 report
before that check has run.

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

## Step 1.8 — Unmerged-Branch Check (finds work earlier sessions stranded)

Run this **after** Step 1.75, for the same reason: a branch list read from
stale remote refs answers the wrong question.

Cloud and remote sessions each push a `claude/<slug>` branch and end. Nothing
in that loop asks whether the work became reachable from `main`, so a session
can finish, push, and still leave its work invisible to every session that
follows. **Nothing about stranded work looks stranded** — the tree is clean,
`rev-list HEAD..origin/main` is `0`, and the close-out reads like a success.
Left unchecked this accumulates silently: the 2026-08-08 audit of this hub and
`tlelosa-claude-config` found 16 such branches, holding ADR-010 that another
file already claimed existed, three `knowledge/` files, and a finished
three-part initiative (`docs/specs/2026-08-05-command-center.md`) nobody could
see.

```
git fetch origin --quiet
git for-each-ref --format='%(refname:short)|%(committerdate:short)' refs/remotes/origin
```

Then, for each ref that is not `origin/main` and not `HEAD`:

```
git merge-base --is-ancestor <ref> origin/main
```

A non-zero exit means that branch is **not** contained in `main`.

**Report in Step 3:** the total count of unmerged branches, then detail at
most the **5 oldest** — name, age in days, and commits ahead. Flag anything
older than **7 days** (same threshold as Step 0.5's stale-session rule).
Report a pass in one line too; silence and never-ran look identical.

Three things to get right, each learned the expensive way:

1. **Diff against `origin/main`, not the merge-base.** If `main` has absorbed
   a large merge, a merge-base diff reports tens of thousands of lines that
   already landed — this hub's `main` carries a 68-commit vault re-merge, and
   diffing against the merge-base made every branch look catastrophic.
   `git diff origin/main <branch>` answers the question you actually have:
   what does this branch have that `main` lacks?
2. **Unmerged by ancestry ≠ holding lost work.** Content often lands by
   another path — a rebase, a re-commit, a vault re-merge — leaving a branch
   that looks stranded but is byte-identical to `main`. Verify per-file before
   concluding anything. And when verifying with `grep`, don't filter on
   `--include=*.md`: it silently skips files like `CLAUDE.md.template` whose
   names don't end in `.md`.
3. **Surfacing is not triaging, and never deleting.** Report what is unmerged
   and let Tebello decide. Do not merge, open a PR, or delete a branch from
   this step — an ancestry test is not enough evidence to discard work.

📍 **This step covers this hub's repo.** The live sub-project repos
(`Desktop/Pappa T/`, Operations' `2. SOPS` and `3. Nameplate & Test Sheet`)
have their own remotes and their own default branches — note that `2. SOPS`
is on `master`, not `main`. Step 1.9 already reads their clocks; if one of
them is where the next task lives, run this check there too rather than
assuming this hub's branch list speaks for it.

## Step 1.9 — Cross-Repo Staleness Check (verifies Step 1 before you believe it)

Run this **after** Step 1.75, not before — comparing against a stale local
`main` compares the wrong clock.

`docs/session-log.md`'s final entry was written by a session that has since
ended, and the work it describes usually continued afterwards in a
*different* repo that pushes on its own schedule. **Nothing about a stale
entry looks stale:** `git status` is clean, `rev-list HEAD..origin/main` is
`0`, and the entry reads as a confident, complete close-out. This produced a
wrong resume report three times (2026-08-07; worst case the hub was 5h19m
behind the vault and wrong on three separate facts, including calling a
phase "blocked" whose blocking ADR had already been written, accepted and
built). Under the O-P-C consolidation this is the normal condition, not an
edge case — hub-level docs and the live sub-projects are separate repos by
design. Full reasoning: `knowledge/hub-process.md`.

1. **List the live repos to check.** Take every sub-project named by the
   final `session-log.md` entry and by the `todo.md` "Next task." The repo
   root is not always the project folder, and it is never O-P-C's
   consolidation snapshot — use the live `Desktop/` working copy per the
   📍 convention in `docs/todo.md`:
   - `Desktop/Pappa T/` is **one** repo covering all of its sub-projects
     (TebelloReborn, ai-outreach-agency, …) — check the vault root.
   - `Desktop/Operations/2. SOPS/` and
     `Desktop/Operations/3. Nameplate & Test Sheet/` are their **own**
     separate repos.
   If a named machine isn't reachable from this session, say so in the
   report and skip that repo — never guess at its state.

2. **Compare newest-commit clocks**, one call per repo:

   ```
   git -C . log -4 --format="%h %ci %s"
   git -C "<live project repo>" log -6 --format="%h %ci %s"
   git -C "<live project repo>" status --porcelain=v1 -b
   ```

3. **If the project's newest commit is later than the hub's newest commit
   touching that item, the hub entry is stale** — however complete it
   reads. Don't repeat it. Read that project's own `docs/todo.md` header
   and `docs/session-log.md` final entry and report *those* as current
   state instead.

4. **The `status` line is part of the answer.** The hub can be accurate
   about what was committed and still wrong about what exists — unpushed
   commits, or uncommitted work in the live repo, change the real state.
   Report them; a clean `rev-list` alone is not the whole picture.

5. **Report the outcome either way in Step 3, including a pass.** One line
   is enough ("hub `<sha>` `<time>` ahead of vault `<sha>` `<time>` — hub
   state accurate"). Silence is indistinguishable from not having run the
   check, which is exactly how this went unnoticed three times.

6. **Finding drift does not make reconciling it this session's task.**
   Surface it in the Step 3 report and let Tebello pick. If both files are
   wrong, `knowledge/hub-process.md` gives the direction: bring the
   *authoritative* (project) file current first, then trim the hub entry to
   a pointer at it.

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
- If a candidate task **is** machine-bound but this session **is** that
  machine (e.g. running on Pappa T and the task says "Pappa T only"), check
  `docs/todo.md` for a linked spec under `docs/specs/`. If one exists, say
  so plainly in the Step 3 report ("Spec ready: docs/specs/<name>.md — no
  further research needed, can start immediately") — this is the common
  case now that machine-bound queue items get specs written ahead of time
  from cloud sessions (started 2026-07-29). Don't re-derive a plan from
  scratch if a ready spec already exists.
- This is a labeling check only — don't skip the task, don't silently
  reorder the queue, and don't try to work around the access gap (e.g. by
  guessing at the other machine's folder structure) without Tebello asking
  for that explicitly.

Then proceed to Step 3.

## Step 3 — Report State

Tell Tebello:
1. **Last completed task** — from `session-log.md`, **as verified by Step
   1.9**, not as the entry states it
2. **Next pending task** — from `todo.md`, with which project (if any) it
   touches
3. **Spec status** — does a spec exist in `docs/specs/` (or the project's
   own `docs/specs/`) for the next task, if it's a build task?
4. **Hub state** — Step 1.9's result, stated explicitly whether it passed
   or found drift
5. **Branch state** — Step 1.8's result, stated explicitly whether it
   passed or found unmerged branches
6. **Known risks** — surface the OneDrive/git item from `CLAUDE.md` if
   still unresolved
7. **Blockers** — anything unresolved, pending decisions, or missing
   context

Format:

```
## Session Resume

**Scope:** [Hub-level | <project folder name>]
**Last completed:** [task name]
**Next task:** [task name from todo.md — if machine-bound and unreachable from this session, say so here: "⚠️ requires local access on <machine> — not runnable from this session"]
**Spec:** [exists at docs/specs/<name>.md | MISSING — must write spec before building | N/A]
**Hub state:** [Step 1.9 — verified: hub <sha> <time> ahead of <repo> <sha> <time>, entry accurate | STALE: <repo> is <N> ahead of the hub's last write, state above taken from that project's own docs | not checkable: <machine> unreachable from this session]
**Branch state:** [Step 1.8 — all remote branches merged | <N> unmerged, oldest <branch> (<days>d, <M> commits ahead) — ⚠️ <K> over 7 days]
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
