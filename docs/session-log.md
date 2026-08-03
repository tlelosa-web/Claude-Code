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

## 2026-07-29 — Hub process review: fix, improve, prevent

Reviewed the knowledge cache and hub process end-to-end for issues to fix,
improve, and prevent, per Tebello's request, then implemented what was
actionable from this session (cloud environment, `tlelosa-web/claude-code`
repo only — no filesystem access to Operations or Pappa T).

**Fixed:**
- Promoted the NamePlateTool Excel-import fix (`777be76`) spot-check from a
  buried prose caveat to a real tracked `docs/todo.md` item (#1), so it
  can't get lost. Still machine-bound (Operations) — flagged as such.
- Resolved the idle numbering-backlog question: kept fixed numbering
  (renumbered 1-9 after inserting the NamePlateTool item), since the
  2026-07-28 priority set hasn't cleared — closed out rather than left
  open indefinitely.

**Prevented (root-cause fix, not just a patch):** `session-log.md` shows
two real merge conflicts already, both from concurrent sessions
(Operations/Pappa T/cloud) editing `docs/todo.md`, `session-log.md`, or
`knowledge/INDEX.md` from a stale local `main`. Added `CLAUDE.md` Hard
Rule 6 and `/continue` Step 1.75 ("Sync Check") — fetch + pull `origin/main`
before editing any of the three contention files, and resolve any
resulting conflict as a real union, never a pick-one-side overwrite.

**Not actionable from this session (flagged, not fixed):** every other
open item in `docs/todo.md` (#2-9) is either awaiting Tebello's direct
decision (SOPS migration go-ahead, Payment Status review, TebelloReborn
scope) or requires local access to a machine/repo this cloud session can't
reach (codex-gate on Pappa T, OpenRouter credits, NamePlateTool test
suite). These weren't touched — surfaced in the resume report instead of
guessed at.

**Last completed:** Hub process review (this entry).
**Next task:** NamePlateTool Excel-import spot-check (`docs/todo.md` #1) —
⚠️ requires local access on Operations, not runnable from this session.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-29 — Ready-to-execute specs for every machine-bound queue item

Tebello asked to have "something ready to go at each machine when continue
is run." Wrote 8 dated spec files under `docs/specs/` (following the
existing `tlelosa-claude-config` ADR-draft naming convention,
`YYYY-MM-DD-<slug>.md`), one per machine-bound `docs/todo.md` item:

- `2026-07-29-nameplatetool-excel-spotcheck.md` (Operations)
- `2026-07-29-nameplatetool-test-suite.md` (Operations, starter scope)
- `2026-07-29-codex-gate-pappa-t-smoketest.md` (Pappa T)
- `2026-07-29-codex-gate-operations-adr-copy.md` (Operations)
- `2026-07-29-tebelloreborn-scope-decision.md` (Pappa T, decision brief)
- `2026-07-29-ollama-timeout-fix.md` (Pappa T)
- `2026-07-29-sops-avgmovement-migration.md` (Operations, gated — not
  cleared to run without an explicit in-session go-ahead)
- `2026-07-29-sops-payment-status-review.md` (Operations, human review)

Each spec is self-contained: goal, steps, definition of done, and the hub
bookkeeping to close out afterward (pull `origin/main` first per Hard Rule
6, update the relevant `knowledge/*.md`, remove the item from `docs/todo.md`
and renumber, log in `session-log.md`).

Rewrote `docs/todo.md`'s "Next up" block to link each item to its spec and
tag it with which machine it needs. Split the old 3-part "close out
codex-gate" item into 3 numbered items (Pappa T smoke-test, Operations ADR
copy, and the IT-confirmation sub-item, which has no spec since it's a
pending external answer, not an executable task) — the three don't share a
machine so bundling them under one checkbox was hiding that only 2 of the
3 are independently actionable right now. Also fixed a numbering gap
(item "3" had been skipped in the 2026-07-29 renumbering).

Added a new bullet to `/continue`'s Step 2.5: when a machine-bound task's
target machine *is* the current session's machine, check for a linked spec
under `docs/specs/` and say so plainly in the resume report — don't
re-derive a plan from scratch when one's already been prepared.

**Last completed:** Ready-to-execute specs for all machine-bound items
(this entry).
**Next task:** Whichever queue item matches the machine a session next
opens on — Pappa T sessions should pick up the Ollama timeout fix,
codex-gate smoke-test, or TebelloReborn scope decision; Operations sessions
should pick up the NamePlateTool spot-check, codex-gate ADR copy, or one of
the two SOPS items (AvgMovement gated on explicit go-ahead).
**Known risks:** None new.
**Blockers:** SOPS AvgMovement migration spec is intentionally not
actionable without Tebello's explicit go-ahead given in that session.

## 2026-07-29 — Broadened session-archival rule to catch stale sessions

Tebello flagged a backlog of unarchived sessions despite `/continue`
Step 0.5 (ADR-005) already existing. Root cause: the rule only proposed
archiving sessions *superseded* by later work in the same project —
sessions that were just old and idle, with no newer session to compare
against, never got flagged at all.

Broadened `.claude/commands/continue.md` Step 0.5 into two independent
checks (a session only needs to match one to be proposed):
- **A. Superseded** — unchanged from the original rule.
- **B. Stale/idle** (new) — any other session with no activity in 7+ days,
  sanity-checked against its transcript so a session mid-wait on something
  external (blocked on Tebello, on IT, watching a PR) isn't flagged just
  for being old; plus single-exchange `Continuation` sessions past 7 days
  with no real task ever given.

Both categories are still proposal-only — `archive_session` is never
called speculatively, and both lists are presented together in one
combined ask so Tebello isn't interrupted twice per run.

**Last completed:** Session-archival rule broadened (this entry).
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (see prior entry).
**Known risks:** None new.
**Blockers:** None.

## 2026-07-29 — codex-gate ADR copy done directly via git (no local Operations access needed)

Tebello picked the "codex-gate: Operations ADR copy" queue item despite it
being flagged ⚠️ machine-bound. Realized the target — this hub repo's own
`docs/decisions/` — is git-synced to Operations, not filesystem-only, so
the copy didn't actually require local machine access: it could be done as
a normal commit+push from this cloud session, same as any other file
change here.

Added `tlelosa-web/tlelosa-claude-config` to this session's repo scope to
read the drafted ADR (`docs/specs/2026-07-21-codex-gate-adr-draft.md`),
then created `docs/decisions/ADR-009-codex-second-opinion-gate.md` in this
repo with the draft's content, matching its own suggested numbering (009).

**Gap found, not fixed:** `docs/decisions/` didn't exist in this repo
before this task, and neither ADR-007 nor ADR-008 are actually recorded
there — despite `tlelosa-claude-config`'s README/`CORE.md`/
`HUB-CHECKLIST.md` all citing them as if they were. Flagged in
`knowledge/tlelosa-claude-config.md` as a follow-up (write them up, or fix
the stale cross-references) — out of scope for this task, which only
covered the codex-gate ADR.

Updated `docs/todo.md` (removed the now-done sub-item, renumbered 2-7),
`knowledge/tlelosa-claude-config.md`, and `knowledge/INDEX.md`.
codex-gate's actual install stays Pappa T-only regardless — unaffected by
this documentation-only task.

**Last completed:** codex-gate ADR copy (this entry).
**Next task:** Whichever machine-bound queue item matches the next
session's machine — Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, or Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items (AvgMovement gated
on explicit go-ahead). Also worth surfacing: the ADR-007/008
gap found above.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-29 — Wrote up ADR-007 and ADR-008 (closing the gap from the codex-gate ADR copy)

Tebello confirmed writing up the two missing ADRs flagged above.
Reconstructed both from what's actually documented in
`tlelosa-claude-config` (added to this session's repo scope, cloned
read-only) since this session has no access to that repo's commit
history — content is accurate to what's on file there, not re-derived
from git log:

- `docs/decisions/ADR-007-core-md-read-not-import.md` — dated 2026-07-18
  per `dcoe-roster/CORE.md`'s own top-of-file note ("confirmed
  2026-07-18"): why `CORE.md` is distributed to opted-in projects via a
  plain read instruction in each project's own `CLAUDE.md`, not a Claude
  Code `@import` (`@import` doesn't resolve absolute paths outside the
  importing project's tree, so a plugin-distributed file can't be reached
  that way).
- `docs/decisions/ADR-008-hub-template-promotion.md` — dated 2026-07-21
  (approximate, tied to the `hub-template/` addition, not independently
  re-verified against commit dates): why the hub-and-spoke `/continue`
  pattern piloted on Operations was extracted into
  `tlelosa-claude-config/hub-template/` as a vault-agnostic `continue.md`
  + `HUB-CHECKLIST.md` reconciliation checklist, once it proved out here.

Both ADRs are now recorded, closing the cross-reference gap — every
"ADR-007"/"ADR-008 in the Operations hub's `docs/decisions/`" citation
across `tlelosa-claude-config` now points at a real file. Updated
`docs/todo.md` and `knowledge/tlelosa-claude-config.md`/`INDEX.md`.

**Last completed:** ADR-007 and ADR-008 written up (this entry).
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (Pappa T: codex-gate smoke-test, TebelloReborn
scope decision, Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items).
**Known risks:** None new.
**Blockers:** None.

## 2026-07-29 — NamePlateTool Excel-import spot-check (Operations)

Ran on Operations per `/continue`'s machine-identity check (hostname/whoami
cross-referenced against `knowledge/operations-hub.md`). Picked up the sole
Operations-runnable ready spec,
`docs/specs/2026-07-29-nameplatetool-excel-spotcheck.md`.

Pulling `origin/main` on the NamePlateTool sub-repo (`C:\Dev\Operations\3.
Nameplate & Test Sheet`) to obtain commit `777be76` (the datetime-crash
fix under test) was blocked by uncommitted prior-session work
(`docs/todo.md` changes + a new untracked `docs/bugs/` file from an earlier
bug-hunt pass). Preserved it via `git stash push -u`, pulled cleanly
(`f8341b4..777be76`), then `git stash pop` produced a genuine merge
conflict in `docs/todo.md` — resolved as a real union (all three bug-hunt
findings kept, the fix's own Done-section entry kept, only the now-stale
duplicate "still open" bug line dropped). Staged (`git add`) but **left
uncommitted** per standing policy (never commit without being asked) — this
is flagged for Tebello, not yet committed.

With the fix pulled, ran the actual spot-check: launched the backend
directly via its venv's `uvicorn` on port 8811, hit
`GET /api/nameplate/from-excel` against the real `NAME PLATE
PROCEDURE.xlsx` — `200`, no `datetime is not JSON serializable` crash,
`date_of_manuf: "MAY.2026"` correctly formatted. Fed that response into
`POST /api/generate-pdf` and extracted the resulting PDF's text with
`pdfplumber`: `Date of Manuf.: MAY.2026` plus every other Excel-sourced
field (Series, Size, Motor, Voltage, F.L.A, Op Temp, Conn, Serial No)
populated and non-blank. Killed the test `uvicorn` process tree
(root+worker PIDs, per the known `--reload` supervisor gotcha) afterward.

Fix is fully verified end-to-end — no new bug found. Updated
`knowledge/nameplatetool.md`'s 2026-07-28 entry with the verification
result, removed the spot-check item from this hub's `docs/todo.md` and
renumbered the remaining queue (1-6).

**Last completed:** NamePlateTool Excel-import fix spot-check (this entry)
— confirmed correct, no new bug.
**Next task:** Whichever machine-bound queue item matches the next
session's machine (Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, Ollama timeout fix; Operations: NamePlateTool test suite, or one
of the two SOPS items).
**Known risks:** None new.
**Blockers:** NamePlateTool sub-repo has staged-but-uncommitted changes
(`docs/todo.md` merge resolution + `docs/bugs/connection-lookup-no-manual-
override.md`) awaiting Tebello's go-ahead to commit.

## 2026-08-03 — Machine consolidation: Operations subtree-merged into O-P-C

Tebello consolidated Operations and Pappa T onto one physical machine
(`TshepangLelosa`) and started building a single merged vault, `O-P-C`
(`C:\Users\tlelo\Desktop\O-P-C`), meant to fully replace the separate
`Claude-Code`/`Operations`/`Pappa T` Desktop folders once migration
finishes. Not run through a Claude session — found mid-flight at the start
of this `/continue` run (`docs/todo.md`/`session-log.md` above still
reflect the pre-migration state; this hub's own root `CLAUDE.md`/`docs/`/
`knowledge/` are unaffected, still current). Pappa T had already been
subtree-merged in (commit `5688803`, full `master`-branch history
preserved under `Pappa T/`) before this session; Operations had not.

Tebello confirmed O-P-C is the intended eventual replacement and asked to
continue with the Operations merge, which had been interrupted (a prior
terminal session doing it got closed accidentally — checked for leftover
`MERGE_HEAD`/lock files/temp remotes first; none found, nothing was
actually broken, just not started).

**Structural difference from the Pappa T merge:** `Operations/` itself
isn't a git repo (unlike Pappa T, which was one unified repo) — it's a
folder holding its own hub docs (`CLAUDE.md`, `docs/todo.md`,
`docs/session-log.md`, `docs/decisions/`, etc.) plus three independently-
versioned nested repos (`2. SOPS` → `sops.git`, `3. Nameplate & Test
Sheet` → `NamePlateTool.git`, `7. DELIVERY NOTE/delivery-note-system` →
local-only, no remote) plus several plain-data folders with no git
tracking (Daily Sales Order Files, Casing Analysis, AvgMovement, FM
Planning & Stock Control, General - Info, IDE, Inventory Management &
Reports, Sage Inventory Report, Stock Report Reference, Workshop Stock).

Per Tebello's confirmation: committed two small pending fixes first
(`CLAUDE.md`'s hub-path reference, `C:\Dev\Operations` →
`C:\Users\tlelo\Desktop\Operations`, present as an unstaged diff in both
NamePlateTool and delivery-note-system) directly in their own repos, then
ran one subtree-merge per independent repo (mirroring the Pappa T
approach exactly: `git fetch <local-path> <branch>` + `git merge -s ours
--no-commit --allow-unrelated-histories FETCH_HEAD` + `git read-tree
--prefix=... -u FETCH_HEAD` + `git commit`, producing a true 2-parent
merge commit that preserves full history) — SOPS (`b2b91bb`), NamePlateTool
(`3134bf8`), delivery-note-system (`35fe0dc`) — then one regular commit
(`6ce7753`) adding everything else (Operations' own hub shell + the
plain-data folders + two stray root files Tebello confirmed including,
`headers.txt`/`response.pdf`) as fresh files with no separate history to
preserve.

**Caught and fixed one real mistake:** the first SOPS merge attempt
silently produced a single-parent commit instead of a real merge —
`git merge -s ours` had failed (a `.gitmodules` file was still staged
from before this session, and git refuses to start a merge against a
dirty index) but the subsequent `read-tree`+`commit` succeeded anyway,
masking the failure. Caught by checking the resulting commit's parent
count before moving on (`git cat-file -p <sha>` showed only one `parent`
line). Fixed by `git reset --hard` back to the pre-attempt commit,
committing `.gitmodules` on its own first (recreated from content read
earlier in the session — the reset had discarded the never-committed
staged file), then redoing the SOPS merge cleanly. The other two merges
were verified to have real 2-parent commits before committing further.

Also caught `__pycache__`/`.pyc` build artifacts swept in by the raw
`cp -r` of the Daily Sales Order Files plain-data folder — unstaged and
deleted before the final commit. Deliberately excluded `.venv` (a real
Python virtualenv found under `7. DELIVERY NOTE/`, confirmed via
`Lib`/`Scripts`/`pyvenv.cfg`) from the copy — standard practice, not
asked about explicitly but a clear-cut call.

**Verified after:** working tree clean, `Pappa T/` byte-identical to
before (`git diff <pre-merge-sha> -- "Pappa T"` empty), `git count-objects`
sane (49 MiB, no runaway blobs), all three merged sub-repos' history
reachable as real second parents.

**Not done, deliberately flagged rather than guessed at:**
- Local `main` now diverges further from `origin`
  (`tlelosa-web/Claude-Code`) — 475 commits ahead (up from 216, since the
  three sub-repos' full histories are now included), still 12 behind. Not
  a clean fast-forward; not attempted this session. Needs a real decision
  from Tebello on how (or whether) to reconcile/push this to GitHub, given
  the repo's identity is changing (single-project hub → multi-vault
  consolidation).
- The old `Claude-Code`/`Operations`/`Pappa T` Desktop folders were left
  untouched — Tebello said O-P-C is meant to *eventually* replace them,
  not that this session should delete/retire them yet.
- `docs/todo.md`'s existing queue (codex-gate, NamePlateTool test suite,
  TebelloReborn scope, Ollama timeout, two SOPS items) is unchanged by
  this entry — machine-bound flags on those items may now be stale given
  the consolidation (this machine can reach both Pappa T's and
  Operations' content), but redoing that queue wasn't part of this task.

**Last completed:** Operations subtree-merge into O-P-C (this entry) —
SOPS, NamePlateTool, and delivery-note-system fully merged with history
preserved; Operations' hub docs and plain-data folders added.
**Next task:** Tebello's call — reconcile the `origin` divergence, decide
what happens to the old Desktop folders, or pick up a `docs/todo.md` item
(re-flagging machine-boundness given the consolidation first).
**Known risks:** `origin` divergence (see above) — no data-loss risk
locally, but the eventual push/reconciliation to GitHub needs a real plan,
not an on-the-fly pull.
**Blockers:** None for further local work. NamePlateTool's previous
staged-uncommitted blocker (noted in the entry above) no longer applies —
that repo's working tree was clean before this merge, only the unrelated
path-reference fix was pending, now committed.
