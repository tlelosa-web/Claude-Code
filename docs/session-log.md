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

## 2026-07-31 — pitwall-companion: workbook audit + interactive Loadouts picker

Ran `/continue`; the machine-bound queue items (Operations/Pappa T) weren't
runnable from this cloud session, so Tebello redirected to project-specific
work on `pitwall-companion` instead (no queue item, no `docs/todo.md` of its
own — a fresh ask, not from this hub's backlog).

**Audit:** Compared the app's embedded driver/part/stat/Series/rewards data
against the community "F1 Clash 2026 Resource Sheet" Google Sheet workbook.
Two versions existed in Drive — v1.0 (Tebello's own copy, more recently
edited, 2026-07-16) and v1.1 (a shared copy from the original author,
2026-05-13, not touched since shared) — confirmed with Tebello that v1.1 is
the intended source of truth despite the older modified-date. Delegated the
full cross-check to a background agent (workbook export too large — 230KB+
— for main-context reading) against `index.html`'s `REF`/`REWARDS`/
`COMPONENT_GROUPS`/`LOADOUT_STRATS` structures. Result: fully in sync — no
missing drivers, parts, stats, Series, or CCData/rewards constants. Confirmed
the workbook has no "Premium Crates" tracker concept at all (a related but
separate community sheet), so the app isn't missing that; confirmed "Asset
Trading surplus" is an app-original feature not sourced from the workbook,
consistent with the README's own framing.

**Feature change:** Tebello wanted the Tools → Loadouts view (screenshot:
`Loadout SS.png` in Drive) to stop requiring a scroll through 9 stacked
preset-strategy cards. Since `bestLoadout(strat)` already accepted an
arbitrary attribute array, this only needed a rendering/state change:
- Replaced the hardcoded `LOADOUT_STRATS` (9 fixed Speed/Cornering/Power
  Unit/Qualifying combos) with `LOADOUT_ATTR_NAMES`, a 4-button multi-select
  toggle bar (Speed, Cornering, Power Unit, Qualifying — Pit Time excluded,
  it's a lower-is-better stat never used as an optimization target).
- `suggestLoadoutsHTML()` now renders exactly one `.lo-card` for whatever
  combination is toggled on, instead of one card per preset.
- Added a guard so the last selected attribute can't be deselected (always
  ≥1 selected, so a card always renders).
- New `LOADOUT_ATTRS_KEY`/`LOADOUT_ATTRS_SCHEMA` localStorage entry
  (matching the existing `STORAGE_KEY`/`SEASON_KEY`/`BOOST_KEY` schema-guard
  convention) persists the selection across reloads — confirmed multi-select
  and persistence both requested explicitly by Tebello over the alternative
  (single-select, reset-on-reload).

Verified with a headless-Chromium smoke test (playwright, served via
`python3 -m http.server`, since no project run-skill existed for this static
PWA): single-card render at all times, multi-select combining correctly
(Speed+Qualifying → one card with both stats highlighted), the last-attribute
deselect guard holding, selection surviving a page reload, and zero
console/page errors. Screenshot confirmed visually.

Pushed to `claude/continuation-8iamwu`, merged as PR #9
(tlelosa-web/pitwall-companion). Then updated `README.md`'s "Tools tab
(coach)" Loadouts description and its "Loadouts are computed from your
collection" design-rationale note to match the new interaction (still
described the old 9-strategy list) — required restarting the feature branch
from the newly-merged `main` first (branch had been reused post-merge, per
this hub's merged-PR convention), force-with-lease pushed since the old
pre-merge history was already fully merged. Merged as PR #10.

**Last completed:** pitwall-companion workbook audit (in sync, no gaps) +
interactive Loadouts attribute picker, merged as PR #9 and #10 (this entry).
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items). See `docs/todo.md`.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-31 — pitwall-companion: polish batch (icon fix, rename, grid layouts)

Follow-up to the Loadouts picker above, same session continuing on
`pitwall-companion` at Tebello's direction (still not a hub queue item — no
`docs/todo.md` of its own).

**Header icon + title centering.** Tebello pointed out from a screenshot that
the header's small icon didn't match the real app icon. Traced it to
`index.html`'s `<header>`: the small `.logo` box was still rendering a
leftover inline `<svg>` placeholder (a rounded square with an X) from before
commit `95834b8` ("Replace app icon with new pit-wall dashboard artwork")
swapped in the real `icons/icon-192.png` cockpit artwork — that commit only
ever updated the actual icon files, never the header's own hardcoded markup.
Replaced the inline SVG with an `<img src="./icons/icon-192.png">`. Also
centered the header title (was left-aligned next to the icon) by changing
`.brand` from a flex row to a `1fr minmax(0,auto) 1fr` grid, so the title
centers on the full header width regardless of the icon/Install-button
widths — verified truncation/ellipsis still behaves correctly at a 320px
viewport.

**Renamed the app to "PitWall Companion."** Tebello flagged a copyright
concern: the app's own name, "F1 Clash Resource Sheet," leaned directly on
the game's trademark rather than just describing what it tracks. Grepped the
whole repo for every occurrence and split them into two categories:
- Renamed (the app's own branding): `<title>`, header text,
  `apple-mobile-web-app-title` (→ "PitWall", matching manifest
  `short_name`), `manifest.webmanifest`'s `name`/`short_name`, the
  exported-backup filename (`f1clash-backup-*.json` → `pitwall-backup-*.json`)
  and its `app:` tag, the QR code's alt text, `sw.js`'s file-header comment,
  and `README.md`'s top-level heading.
- Left alone (nominative/factual, not the app's own branding): mentions of
  the F1 Clash game itself and the community "F1 Clash 2026 Resource Sheet"
  workbook the app is built from — already covered by the existing
  "unofficial fan tool, not affiliated with F1, Formula 1, or Hutch Games"
  disclaimer. Also left the internal `localStorage` keys
  (`f1sheet.v1`/`f1sheet.season.v1`/`f1sheet.boosted.v1`/
  `f1sheet.loadoutAttrs.v1`) and the service-worker `CACHE_VERSION` string
  untouched — these aren't user-visible, and renaming them would silently
  wipe every existing user's saved card levels/season data/boosts on their
  next visit (a new key means `load()` finds nothing under the old name).
  Flagged this reasoning explicitly rather than silently deciding it.

**Loadouts grid layouts.** Two follow-up screenshots from Tebello showed the
attribute-toggle buttons and the aggregate stat chips both wrapping unevenly
(flex-wrap sizing each pill to its own text — "Speed"/"Qualifying" full-width,
"Cornering"/"Power Unit" narrow). Changed `.lo-attr-bar` (4 buttons) to a
`1fr 1fr` grid for an equal-size 2x2 layout, and `.lo-aggs` (5 stat chips:
Speed/Cornering/Power Unit/Qualifying/Pit Time) to the same `1fr 1fr` grid
for an equal-size 2x3 layout (last cell empty) — both requested explicitly
as "equal size" grids, not just reflowed.

All three changes verified with headless-Chromium screenshots (playwright,
served via `python3 -m http.server`) before pushing — icon match, centered
title at two viewport widths, `document.title`/header text reading "PitWall
Companion", and both grids rendering as equal-width cells — zero console
errors in every check.

Pushed to `claude/continuation-8iamwu` as three separate commits, then
combined into one PR per Tebello's request ("combine all PRs") since none of
the three had been opened as a PR yet — merged as PR #11
(tlelosa-web/pitwall-companion). The stat-chip grid fix came as a fourth,
later request after #11 was already merged, so it shipped as its own PR #12
rather than being folded in retroactively.

**Last completed:** pitwall-companion header icon fix + "PitWall Companion"
rename + Loadouts 2x2/2x3 equal-size grids, merged as PR #11 and #12 (this
entry).
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items). See `docs/todo.md`.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-31 — pitwall-companion: Loadouts By Track, Suggested Boost, Boosts tab

Same session, continuing on `pitwall-companion` — a substantially bigger
round than the polish batch above, still at Tebello's direction and still
not a hub queue item.

**Real F1 2026 calendar research (dead end, kept for context).** Tebello
asked for a deep web search on 2026 season tracks and stats; WebFetch was
broadly broken this session (even `example.com` 403'd through the agent
proxy, unrelated to any specific site), so the audit ran entirely on
WebSearch's synthesized results instead, publishing a 24-round circuit
reference artifact with sourced caveats (a genuine "two Spain rounds"
ambiguity in the sources, Madrid having no race-history stats pre-debut).
Turned out to be the wrong "tracks" — Tebello meant the F1 Clash **game's**
in-game circuits, not the real calendar. Pivoted immediately; the real-world
artifact was informational only, no code impact.

**In-game Track Stats + expanded per-track detail.** Tebello sent 21
in-game "Track Stats" screenshots (one driver stat + one component stat
spotlighted per circuit); transcribed them into a new `TRACKS` array and
shipped as a 4th Tools tab first (PR #13), then — per explicit feedback that
a separate tab duplicated Loadouts at lower detail — moved into Loadouts
itself as a **mode switch** ("By Attribute" / "By Track", `loadoutMode`
state). By Track adds a 21-circuit dropdown (`loadoutTrack`, persisted); for
the selected track it shows the best 2 owned drivers for the driver stat in
a 1x2 grid (per an approved mockup screenshot before building), and the same
full Loadouts-style card as before for the component stat. Extracted
`loadoutCardHTML()` so both modes render identical card markup.

**Suggested Boost.** Added a third element to the By Track card stack,
between the driver grid and the loadout card: the top 3 *owned* consumable
Boosts (`boostOwned[name] > 0`), ranked by the track's driver stat first and
its component stat as tiebreak (Tebello's explicit scoring rule — "top
driver then track, give top 3" — not the sum-of-both-stats approach
initially proposed). Verified the ranking logic against real data
(Eclipse/Skull tied on Overtaking, correctly tiebroken alphabetically ahead
of Full Send and excluding zero-Overtaking Champion).

**Boosts-ownership tab + New Boost custom entries.** The app had Boosts
*data* (65 named consumable boosts, flat bonuses) but no ownership tracking
at all — Suggested Boost needed it. New 4th Tools tab "Boosts": a dropdown
picker (not a 65-row scroll, per explicit feedback) shows one boost's stats
+ a quantity-owned input at a time. Added a **New Boost** form since "the
game keeps adding boosts" faster than any static list can track — full
13-stat vocabulary exposed per Tebello's "all attributes need to be
available" requirement, blocked from colliding with a built-in boost's name
(re-adding an existing custom name edits it instead), and merged with the
built-in list via `allBoosts()` so custom entries compete in Suggested Boost
rankings exactly like built-in ones — this was an explicit yes from Tebello,
not assumed.

**4 newly-discovered boosts.** Tebello sent 8 more screenshots of their own
Boosts collection ("add any new boosts you discover... do not seed my
quantities"). Cross-referenced all names against the existing 65 and found
4 genuinely new: Livewire Plus, Midnight, Mushroom, Succession. Decoded
their stat values by building an icon-shape legend from ~15 already-known
boosts in the same screenshots (icon shape is consistent across boosts;
background color varies per-boost and isn't semantically tied to a stat) —
high confidence on 3, but flagged Mushroom's Impact/Recharge assignment as
uncertain (both use a visually similar "bolt + small accent" icon, only one
reference example each to cross-check against). Tebello confirmed via an
in-game screenshot of the Mushroom card that the guess was exactly right
(Power Unit +25, Impact +10, Recharge Rate +15) — no changes needed. Added
all 4 to the built-in `BOOSTS` array only; deliberately did not seed any
owned quantities, per explicit instruction.

**README overhaul.** Before merging, Tebello asked for a completeness audit
("this is a big update"). Found README had gone stale across the last few
merges — still described single-mode Loadouts, no mention of the Boosts tab
or Track Spec at all, and undercounted boosts at 65 instead of 69. Rewrote
the Loadouts/Tools section, added the 3 new localStorage keys
(`f1sheet.loadoutAttrs.v1` extended with mode/track, `f1sheet.boostOwned.v1`,
`f1sheet.customBoosts.v1`) to the storage-keys list, and added data-notes
entries documenting that Track Stats and the 4 newest boosts are hand-
transcribed from in-game screens, independent of either workbook version.
Also ran a full regression pass across every tab (Drivers, Parts, Season,
Rewards, all 4 Tools sub-tabs) before considering the audit done — zero
console errors, confirmed empty-states render properly.

**Real merge conflict on `git merge` (not just a stale-base warning this
time).** PR #14 hit an actual GitHub merge conflict — the branch's merge-base
with `main` was `140da68`, several merges behind (PRs #11/#12/#13 were
squash-merged into `main` as new commits the branch never rebased onto,
since each round just kept pushing to the same long-lived branch instead of
restarting from `main` after every individual merge). Resolving it surfaced
a real bug, not just textual noise: git's 3-way merge silently
**resurrected** the old, already-deleted standalone Tracks-tab code
(duplicate `const TRACKS` / `function tracksHTML` declarations) without
flagging it as a conflict, because the diff hunks didn't textually overlap
even though they were semantically contradictory (my branch's deletion vs.
`main`'s still-present copy from the already-merged PR #13). A plain
`git diff`/visual check wouldn't have caught this — it was only visible by
actually trying to execute the merged file: `node --input-type=module -e
"new Function(scriptContents)"` threw `SyntaxError: Identifier 'TRACKS' has
already been declared`. Removed the resurrected block, re-ran the full
regression suite to confirm the final merged file matched pre-conflict
behavior, then completed the merge commit. Worth remembering for next time a
long-lived branch survives multiple squash-merges of its own prior PRs:
either restart it from `main` after each merge, or run an executability
check on any conflict resolution before trusting a "no conflict markers
left" visual pass.

Merged as PR #14 (tlelosa-web/pitwall-companion), squash commit `3c940ae`.

**Last completed:** pitwall-companion Loadouts → By Track + Suggested Boost +
Boosts-ownership tab + 4 new boosts + README overhaul, merged as PR #14
(this entry).
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items). See `docs/todo.md`.
**Known risks:** None new.
**Blockers:** None.

## 2026-07-31 — pitwall-companion: Loadouts By Track loadout customization + Discord share

Final pitwall-companion round of the day, same session. Tebello asked for
the By Track loadout to be customizable "the same way the loadout tab
works" — the loadout card there had been locked to the track's single
official component stat since PR #14, with no way to tweak it like By
Attribute mode's toggle buttons allow.

**Design questions asked before building** (three real forks, all answered
with the recommended option): (1) should the By Track attribute selection
share state with By Attribute mode, or stay independent — independent won;
(2) should switching tracks reset the selection to that track's own stat,
or carry over whatever was picked — reset-per-track won; (3) should the
driver ranking / Suggested Boost also follow the custom selection, or stay
tied to the track's real in-game stat regardless — stay-tied won, so only
the loadout card itself became adjustable, not the parts of By Track that
reflect actual game data.

**Implementation:** new `trackLoadoutAttrs` Set + `trackLoadoutAttrsFor`
(records which track the current selection belongs to, so `trackSpecHTML()`
can detect a track change and reset), both persisted in the same
`f1sheet.loadoutAttrs.v1` key alongside the existing By Attribute state. New
toggle bar (`data-tlattr`) reuses the same `LOADOUT_ATTR_NAMES` list and
`loadoutCardHTML()` helper as By Attribute, so the two modes render
identically despite separate underlying state. Verified with a headless
test: Abu Dhabi defaults to just Speed, adding Cornering updates the card
live, switching to Monaco resets to just Cornering (Monaco's own stat), By
Attribute's selection stays untouched throughout, and everything persists
across reload.

**Merge conflict, again — same root cause as PR #14.** PR #15 hit the exact
same class of conflict: the branch's merge-base with `main` was still
several squash-merges behind (this branch has now survived 4 of its own
prior PRs — #11 through #14 — without ever restarting from `main` in
between). Applied the same fix as last time: resolved each conflicted
region by keeping the branch's newer code, then didn't stop at "no conflict
markers left" — ran the same `node --input-type=module` executability
check, plus a duplicate-top-level-declaration grep this time
(`grep -oE '^(const|let|function) [A-Za-z_]+' index.html | sort | uniq -c`)
as a faster way to catch the same resurrected-dead-code failure mode before
it reaches Tebello. Also diffed the pre-merge-commit tree against the final
squash commit (`git diff 872b0b1 f01e705 -- index.html README.md`) to
positively confirm zero content difference despite `git merge-base
--is-ancestor` reporting false — a reminder that ancestry checks don't
apply across squash merges (each one creates a brand-new, parentless-in-
practice commit even when the tree content is identical); a content diff is
the only way to actually confirm nothing was lost in that situation, not an
ancestry check. Merged as PR #15, squash commit `f01e705`. Re-verified
against a fresh `main` checkout (not just the merge commit) with both the
full regression suite and the feature-specific test before calling it done,
then reset the local branch to match `origin/main` so the next session
starts from a clean, unambiguous base instead of another stale long-lived
branch.

**Discord share.** This was the last pitwall-companion change planned for
today — Tebello is sharing the app with their Discord server's trusted
testers for a week-long trial before a wider community launch. Wrote an
introductory message for the server owner to post, describing the app,
what's new, and the trial framing (see the message itself for content —
not duplicated here since it's conversational output, not a finding).

**Last completed:** pitwall-companion Loadouts → By Track loadout
customization, merged as PR #15 (this entry) — app then shared to Discord
for a trusted-tester trial week.
**Next task:** Unchanged — whichever machine-bound queue item matches the
next session's machine (Pappa T: codex-gate smoke-test, TebelloReborn scope
decision, Ollama timeout fix; Operations: NamePlateTool spot-check,
NamePlateTool test suite, or one of the two SOPS items). See `docs/todo.md`.
Watch for early feedback from the Discord trial that might reprioritize
pitwall-companion work above the machine-bound queue next session.
**Known risks:** None new.
**Blockers:** None.
