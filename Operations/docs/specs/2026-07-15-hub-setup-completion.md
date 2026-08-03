# Hub Setup Completion — Execution Plan

**Origin:** "Fan Movement workspace setup" session (2026-07-15) — root hub DCOE
setup + OneDrive/git relocation. That session closed out with five loose ends
tracked in `docs/todo.md` § Next up. This spec sequences and closes them out.

**Author:** Context/Planner pass, root hub session, 2026-07-15.

-----

## Item 1 — Stale `.git` lock artifacts in `2. SOPS`

**Status:** Ready to execute now. Verified before acting:
- `git status --short` on `2. SOPS` is clean (one pre-existing unrelated
  edit to that project's own `docs/todo.md`, not touched by this plan).
- `git fsck` shows only harmless dangling objects, no `bad object` errors —
  repo is healthy.
- No git process holds these locks; they are dead artifacts pre-dating the
  OneDrive fix.

**Files to delete** (12 files, all 0 bytes, in `2. SOPS/.git/`):
`HEAD.lock.bak`, `HEAD.lock.bak.1`, `HEAD.lock.bak.r1`,
`HEAD.lock.bak.11381`, `HEAD.lock.bak.16091`, `HEAD.lock.bak.18229`,
`HEAD.lock.bak.20003`, `index.lock.bad`, `index.lock.bak`,
`index.lock.bak.1`, `index.lock.bak.12754`, `index.lock.bak.18359`,
`index.lock.bak.26592`, `index.lock.bak.29139`, `ORIG_HEAD.lock.bak.8732`
(15 total — todo.md undercounted).

**Found but out of original scope:** `next-index-12.lock` (12.4 KB) and
`next-index-13.lock` (12.6 KB) — non-zero content, not named in the original
todo item. Flagging separately rather than deleting blind; recommend
confirming these are also dead (they predate this session and `fsck`/`status`
are clean, so almost certainly safe) before removing.

**Action:** delete the 15 confirmed dead files now. Ask before touching the
two `next-index-*.lock` files.

-----

## Item 2 — `Operations.old-onedrive-backup` disposition

**Status:** Blocked on a decision only Tebello can make (hub `CLAUDE.md`
hard rule 4 — ask before deleting/moving anything under a project's data
paths; this is the whole pre-move tree, so the same bar applies).

**Facts gathered:** 104,390 files, ~2.65 GB, still inside the OneDrive sync
scope at `...\Desktop\Operations.old-onedrive-backup`, consuming cloud
storage on every sync cycle since 2026-07-15.

**Options:**
- Delete outright (safe once confident nothing's needed from it — the live
  tree at `C:\Dev\Operations` is the working copy and has been since the
  move).
- Exclude from OneDrive sync but keep on disk (stops the storage cost,
  keeps a local-only safety copy).
- Keep as-is a while longer (status quo, cost keeps accruing).

**Action:** surfaced to Tebello as a question in this session.

-----

## Item 3 — Confirm OneDrive doesn't recreate `Operations` at the old path

**Status:** Checked now — junction at
`...\Desktop\Operations` still resolves to `C:\Dev\Operations`, created
2026-07-15 (the move date), intact. No recreation has occurred as of this
session.

**Action:** no fix needed. This isn't a one-time close-out — note in
`docs/todo.md` as "verified clean as of 2026-07-15, re-check if OneDrive
sync issues resurface" rather than marking fully done, since a future sync
cycle is still the theoretical risk.

-----

## Item 4 — DCOE rollout order for remaining projects

**Status:** Blocked on Tebello's actual near-term priorities (hub
`CLAUDE.md` hard rule 6 — no project onboards without a deliberate,
recorded decision; backlog item already flagged this: "ask Tebello what the
concrete near-term goals are for each active project").

**Candidates:** `7. DELIVERY NOTE`, `1. Daily Sales Order Files`,
`8. AvgMovement`, `Inventory Management & Reports`,
`3. Nameplate & Test Sheet`.

**Action:** surfaced to Tebello as a question in this session.

-----

## Item 5 — Reconcile pipeline-folder convention with DCOE

**Status:** Blocked on Item 4. The pipeline convention
(`1_Documentation/` → `5_Archive_and_Debug/`) only needs reconciling against
DCOE (`docs/specs/`+`docs/todo.md`) for whichever pipeline project is
onboarded first — doing this in the abstract, before a rollout order
exists, risks designing for the wrong project's actual constraints.

**Action:** defer until Item 4 is answered; becomes the first task of
whichever pipeline project is chosen. Needs an ADR in `docs/decisions/`
per hard rule 6, not a silent convention pick.

-----

## Sequencing

1. Item 1 (lock cleanup) — execute now, no dependency.
2. Item 3 (OneDrive check) — already done, just log it.
3. Items 2 and 4 — ask Tebello now; unblock as soon as answered.
4. Item 5 — starts automatically once Item 4's answer names a project.
