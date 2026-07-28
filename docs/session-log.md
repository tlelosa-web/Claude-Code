# session-log.md — Claude-Code hub

One entry per hub-level session, most recent last. `/continue`'s Step 1
reads only the final entry.

## 2026-07-28 — Cross-project status survey + hub setup

Surveyed all 5 GitHub repos (`Claude-Code`, `tlelosa-claude-config`,
`NamePlateTool`, `cratetracker`, `pitwall-companion`) plus both machines
(Operations, Pappa T) for live status: open PRs, recent commits, and each
project's own `docs/todo.md`. Found zero open GitHub issues anywhere —
tracking runs entirely through `docs/todo.md` files.

Actions taken:
- Merged `tlelosa-claude-config` PR #9 (marketplace validation + plugin
  rollout completion); stopped the hourly watch-loop trigger that had been
  polling it since 2026-07-26.
- Closed this repo's PR #1 as superseded (conflicted with `main`, which
  already carries its own `CLAUDE.md`/`knowledge/` from later merged work).
- Confirmed the Pappa T ↔ cloud-environment sync bridge works end to end:
  cloned this repo on Pappa T, fetched and checked out this session's
  branch.
- Filled the TebelloReborn ("Career Engine") knowledge gap directly from a
  Pappa T session — see `knowledge/pappa-t.md`.
- Published a status dashboard as a Claude Artifact (cross-project
  priorities, machine state, resolved items).
- Set this repo up as the actual DCOE hub root per `hub-template`: added
  `.claude/commands/continue.md`, `docs/todo.md` (this queue), and this
  log; reconciled root `CLAUDE.md` against `hub-template/HUB-CHECKLIST.md`
  (CORE.md read instruction, hub-and-spoke framing, hard-rules note).

**Last completed:** Hub setup (this entry).
**Next task:** Fix the Excel-import bug in NamePlateTool — see `docs/todo.md` #1.
**Known risks:** None new. OneDrive/git corruption fix (Operations) already
holding, see `knowledge/operations-hub.md`.
**Blockers:** None.

## 2026-07-28 — Operations set up as a DCOE hub client

Ran the Operations-side setup prompt (mirrors the Pappa T setup already on
file): confirmed this repo was already cloned on the Operations work PC at
`C:\Dev\Claude-Code` (sibling of `C:\Dev\Operations`, not nested inside
it — keeps `C:\Dev\Operations` itself out of scope for its own hard rule
against becoming a git repo without a separate deliberate decision).
Confirmed clean working tree on `main`, then exercised the sync bridge for
real: `git fetch origin` + `git pull origin main` fast-forwarded 8 files
of genuinely new upstream work (this session's own prior commits — CORE.md
read instruction, `docs/todo.md`, `docs/session-log.md`,
`knowledge/pappa-t.md`, etc.), and `git push origin main --dry-run`
confirmed the push side is clean with nothing outstanding. Read root
`CLAUDE.md` and `knowledge/INDEX.md` per session-start convention. Recorded
the confirmation in `knowledge/operations-hub.md` (new dated entry) and
bumped its `INDEX.md` row.

**Last completed:** Operations DCOE hub-client setup (this entry).
**Next task:** Fix the Excel-import bug in NamePlateTool — see `docs/todo.md` #1.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-28 — Operations vault survey

Ran a full survey of the Operations vault (`C:\Dev\Operations`) to find any
project not yet in `knowledge/INDEX.md`. Enumerated every folder under
`C:\Dev\Operations` and `C:\Dev` directly — confirmed `3. Nameplate & Test
Sheet` is the already-tracked NamePlateTool (same GitHub remote), confirmed
the remaining data-only folders (`4. Casing Analysis`, `Inventory Management
& Reports`, `Sage Inventory Report`, `Stock Report Reference`, `Workshop
Stock - *`, `FM Planning & Stock Control`, `General - Info`, `IDE`) hold no
code, and found three genuinely new projects: `2. SOPS`, `7. DELIVERY
NOTE/delivery-note-system`, and `1. Daily Sales Order Files`.

For each, read its own `CLAUDE.md`/`README.md`/`docs/todo.md` (or
`1_Documentation/USER_GUIDE.md` for the pipeline project) for outstanding
items and reusable technical facts, respecting the no-company-data rule.
Also checked `8. AvgMovement` (already known Retired) — confirmed via
`3_Live_Reports/` timestamps it hasn't produced a report since 2026-05-13;
folded it into `knowledge/sops.md` as a note rather than giving it its own
file, since its logic was ported into SOPS (Batch 32/33) and it has no
independent facts left to track.

Wrote `knowledge/sops.md` (stack/TDD/held-migration convention, stale-dev-
server gotcha, git-worktree/OneDrive history, concurrent-session git
contamination pattern — this last one matches a hazard already on file in
Operations's own project memory, cross-confirming it's a real recurring
risk), `knowledge/delivery-note-system.md` (Next.js 16/Prisma 7 stack,
Prisma-7 driver-adapter gotcha, Turbopack+Windows-junction workaround,
DN-number generation fix), and `knowledge/daily-sales-order-files.md`
(5-stage pipeline shape, load-bearing folder layout, external OneDrive
dependencies, self-correcting filename resolution — healthy project, no
outstanding items). Updated `knowledge/INDEX.md` with all three.

Added two new items to this hub's own `docs/todo.md`: SOPS's held
AvgMovement-migration go-ahead (blocks formally decommissioning
`8. AvgMovement`) and SOPS's Payment Status data-migration review — both
live-data/human-decision items, not code-completion items. Note: SOPS's own
`docs/todo.md` had one stale entry (PO-edit work marked "not yet committed"
as of 2026-07-23) — verified live via `git log`/`git status` that it
actually shipped as commit `46c9acb` (2026-07-24); not carried forward as
an outstanding item, and flagged in `knowledge/sops.md` so a future session
doesn't need to re-verify it.

**Last completed:** Operations vault survey (this entry).
**Next task:** Fix the Excel-import bug in NamePlateTool — see `docs/todo.md` #1.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-28 — Full repo sync-up (get-up-to-speed pass)

After the Operations vault survey, checked all 5 tracked GitHub repos for
activity since the last check. `tlelosa-claude-config`, `cratetracker`, and
`pitwall-companion` are unchanged (same head commits as the earlier
cross-project survey). `NamePlateTool` had one new commit, `777be76`,
pushed 2026-07-28 18:51 UTC in a session outside this hub — it fixes the
Excel-import bug that was this queue's #1 priority: the `datetime`
serialization crash and the dead `"Table 1"` sheet-name check are both
resolved, and root-causes why the 2026-07-17 attempt regressed to blank
fields. Updated `knowledge/nameplatetool.md` (new entry, old open-bug
entries marked superseded) and removed the item from `docs/todo.md`,
renumbering the rest.

Remote Control setup on Operations (started earlier this session) and
Pappa T is deliberately deferred to the weekend per Tebello's direction —
not part of this pass.

**Last completed:** Full repo sync-up (this entry) — NamePlateTool bug
confirmed fixed.
**Next task:** Close out the codex-gate rollout (`tlelosa-claude-config`) —
see `docs/todo.md` #1. Remote Control setup on Operations/Pappa T deferred
to the weekend.
**Known risks:** None new.
**Blockers:** None. One open follow-up: NamePlateTool fix not yet manually
spot-checked against a generated PDF from this session.

## 2026-07-28 — Session end: Pappa T vault survey queued first

Ending this session. Added a Pappa T vault survey as the new #1 priority in
`docs/todo.md`, ahead of the codex-gate item — mirrors the Operations vault
survey done earlier this session (same approach: enumerate project folders
not yet in `knowledge/INDEX.md`, pull reusable facts + outstanding items
into the knowledge cache, fold any genuinely new cross-project tasks into
this queue). Explicit instruction: run this before any other continuation
work picks up next session.

**Last completed:** Full repo sync-up + NamePlateTool bug confirmation
(previous entry).
**Next task:** Pappa T vault survey — see `docs/todo.md` #1. Run first,
before anything else.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-28 — Pappa T vault survey (concurrent second pass)

Ran the same day as the session-end entry above, from a separate Pappa T
session — surveyed that machine for projects not yet tracked here, mirroring
the Operations vault survey pattern.

Actions taken:
- Resolved the `Claude-Code/` "untracked nested repo, unclear origin" flag
  raised by an earlier Pappa T `/continue` run: it's this repo — a
  deliberate, already-pushed sibling folder inside the Pappa T vault
  directory, not a submodule, not stray work.
- Superseded the inline TebelloReborn note the concurrent hub-setup session
  had added to `knowledge/pappa-t.md` with a dedicated
  `knowledge/tebelloreborn.md`, written from a direct read of that project's
  own `CLAUDE.md`/`docs/architecture.md`/`docs/todo.md` — resolves the
  original note's "[scraping specifics unclear from the summary]" gap
  (PNet/Careers24 simply have no dedicated Apify actor yet, per ADR-002) and
  adds the ADR-003 inference-provider-split detail, the doc-gen
  prompt-injection security fix, and the fpdf2/Apify build-time gotchas.
- Added four more Pappa T sub-project knowledge files — none of Pappa T's
  five sub-projects are independent git repos, so none had a dedicated file
  yet: `ai-outreach-agency.md` (surfaced two open items, now in
  `docs/todo.md`), `mims-app.md`, `iq-signal-generator.md`, `tenders-sa.md`.
- Confirmed no other dev-root folder exists on the Pappa T machine. Noted
  `~/OneDrive/` and `~/Documents/Codex/` as data-only (no dedicated file),
  `~/python-sdk/` as a downloaded runtime rather than a project, and the
  extra `~/Downloads/tlelosa-claude-config/` clone as already covered by its
  existing entry (same remote, skipped per the dedupe rule).

Ran concurrently with, and unaware of, the "Session end" entry above that
queued this same survey — both landed on separate branches and are
reconciled in this merge entry below.

**Last completed:** This survey.
**Next task:** Unchanged from the entry above — Fix the Excel-import bug in
NamePlateTool (`docs/todo.md` #1) [later confirmed fixed — see the next
entry].
**Known risks:** None new.
**Blockers:** None.

## 2026-07-28 — Fixed /continue's machine-bound-task blind spot

This session offered the Pappa T vault survey (`docs/todo.md` #1) as
pickable via `AskUserQuestion`, and Tebello confirmed it — only to
discover it's not runnable from a cloud Claude-Code-on-the-web session
(no filesystem access to Pappa T; git is the only sync channel per
`knowledge/pappa-t.md`). Drafted a standalone survey prompt for Tebello to
run in a local Pappa T session instead, mirroring the Operations vault
survey approach from this log's earlier entry — not aware at the time that
the concurrent Pappa T session above had already completed that survey on
its own branch.

Then fixed the root gap in `.claude/commands/continue.md`: added Step 2.5
("Flag Machine-Bound Tasks"), which checks candidate next-tasks against
this session's actual environment before Step 3 reports them, and marks
any machine-bound-and-unreachable item with a ⚠️ note in both the resume
report and its `AskUserQuestion` option — so Tebello sees the access gap
before picking, not after confirming.

**Last completed:** `/continue` machine-bound-task check added (this entry).
**Next task:** Pappa T vault survey — still queued in `docs/todo.md` #1,
to be run by Tebello directly in a local Pappa T session (prompt drafted
this session, not saved to a file — see this entry for where to regenerate
it if needed).
**Known risks:** None new.
**Blockers:** None.

## 2026-07-28 — Merged the Pappa T vault survey into main

The Pappa T vault survey (previous-but-one entry) had landed on a separate
branch (`claude/cloud-env-overview-setup-ymv1vd`) that diverged from `main`
before the Operations vault survey, NamePlateTool bug-fix confirmation, and
Step 2.5 machine-bound-task check were added — so merging it produced six
real conflicts (`.claude/commands/continue.md`, `docs/todo.md`,
`docs/session-log.md`, `knowledge/INDEX.md`, `knowledge/nameplatetool.md`,
`knowledge/pappa-t.md`), all from genuine concurrent work on both sides, not
duplicate edits. Resolved each as a real union rather than picking one side:
kept `origin/main`'s newer `continue.md` (Step 2.5) and `nameplatetool.md`
(clean superseded-chain for the bug fix); combined both branches' `docs/todo.md`
"Next up" items (codex-gate, NamePlateTool tests, TebelloReborn, the two new
ai-outreach-agency items, and the two SOPS items) and moved the now-completed
Pappa T survey to "Done"; combined `knowledge/INDEX.md` into one 14-row table;
kept the Pappa T-survey-completed status on the TebelloReborn note in
`pappa-t.md`. Also reordered this file into genuine chronological order —
the previous `main` history had the "Fixed /continue's machine-bound-task
blind spot" entry sitting first instead of last, which meant `/continue`'s
Step 1 (reads only the final entry) was picking up a stale "next task"
pointer; entries above are now in the order they actually happened, oldest
first, per this file's own header convention. PR #6, merged via GitHub API
merge (not local push to `main`).

**Last completed:** Pappa T vault survey merge (this entry).
**Next task:** Close out the codex-gate rollout (`tlelosa-claude-config`) —
see `docs/todo.md` #1 — currently left open per Tebello's direction pending
further instruction.
**Known risks:** None new.
**Blockers:** None.
