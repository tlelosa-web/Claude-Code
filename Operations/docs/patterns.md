# Cross-Project Pattern Library

> This is how the hub brain (`CLAUDE.md`) "learns" from individual projects.
> A pattern gets listed here once it's proven in at least one real project,
> with a status showing how widely it's been adopted. Nothing here is forced
> onto a project — adoption is always a deliberate per-project decision,
> recorded in that project's own docs or in `docs/decisions/` at root.

-----

## Status legend

- **Proven** — working in production in the source project.
- **Available** — documented here, not yet adopted elsewhere.
- **Adopted (N)** — in active use in N projects beyond the source.

-----

## Patterns

### 1. DCOE four-stage routing (Domain → Context → Orchestrate → Execute)

**Source:** `2. SOPS` | **Status:** Proven, root hub adopted (this file's own
existence is the first adoption)

Never let one agent both plan and build a non-trivial task. Domain confirms
scope → Context/Planner writes a spec to `docs/specs/` → Orchestrator
coordinates → Executors each do one task, one commit, fresh context.

### 2. `docs/todo.md` anti-drift pattern

**Source:** `2. SOPS` | **Status:** Proven, adopted (1) — root hub

Agents rewrite `docs/todo.md` at the end of every task. This pulls current
state into the model's recent-attention window and prevents goal drift
across long sessions, since Claude has no memory between sessions.

### 3. `/continue` session-resume command

**Source:** `2. SOPS` (`.claude/commands/continue.md`) | **Status:** Proven,
adopted (1) — root hub, adapted for multi-project context instead of
Trading/Engineering/Software domain classification.

### 4. User-level agent roster (`~/.claude/agents/`)

**Source:** `2. SOPS` CLAUDE.md v3.2 | **Status:** Proven, already global.
Description now sourced from `CORE.md` (ADR-007) for any project that opts in
via the read instruction — this entry stays as the pattern-library record,
not a second authoritative copy.

The 9-agent roster (domain, planner, architect, executor, tester, reviewer,
doc-writer, debugger, data-agent) is deployed once at user level and applies
automatically in every project folder. Project-level `.claude/agents/` is
reserved for single-agent overrides only — never a full re-fork of the
roster. The standalone `~/.claude/agents/*.md` files remain the actual agent
definitions — `CORE.md` only carries the roster *table* (name, default file,
when-to-use), not the agent bodies themselves, so nothing there is redundant
with these files.

### 5. One task = one atomic commit, via git worktrees

**Source:** `2. SOPS` | **Status:** Proven in SOPS | **Not applicable at root**
(root has no git repo — see `CLAUDE.md` § Known Risk). Relevant once a
project below root adopts DCOE and needs parallel Executor work.

### 6. Pipeline folder layout (`1_Documentation/ → 2_Source_Data/ → 3_Live_Reports/ → 4_Scripts/ → 5_Archive_and_Debug/`)

**Source:** `1. Daily Sales Order Files`, `8. AvgMovement`,
`Inventory Management & Reports`, `3. Nameplate & Test Sheet`
**Status:** Proven, reconciled with DCOE — see
`docs/decisions/ADR-003-pipeline-project-dcoe-convention.md`.

This is a *different* convention from DCOE's `docs/specs/` + `docs/todo.md`
pattern — it's data-pipeline-shaped, not feature-development-shaped. The
folders are load-bearing (hardcoded into scripts) and each project's
`1_Documentation/` guide already carries an informal execution log + fix
history. **Resolution (ADR-003, 2026-07-15):** pipeline projects get a
*lightweight* DCOE onboarding — a project `CLAUDE.md` that documents the
existing layout and defers to it, no parallel `docs/` scaffold. Applied to
`1. Daily Sales Order Files` first; `8. AvgMovement` and
`Inventory Management & Reports` reuse the same convention without
re-deciding it.

### 7. Context budget threshold + handoff

**Source:** Root hub (hub-native, not promoted from a sub-project) | **Status:**
Available — see `docs/decisions/ADR-005-context-budget-and-session-archival.md`

At ~45% context consumed (55% remaining), stop starting new implementation
work, write current state to `docs/session-log.md` + `docs/todo.md`, and
prompt for `/compact` or a fresh session. Self-monitored via `CLAUDE.md` —
no harness hook can read live context percentage, so this only holds if the
agent actually reads and follows the rule. A sub-project can adopt the same
threshold in its own `CLAUDE.md` § Context Management if useful; not forced
on any project by this entry.

### 8. Judgment-based session archival check

**Source:** Root hub (hub-native) | **Status:** Available — see
`docs/decisions/ADR-005-context-budget-and-session-archival.md`

Added as a step in `.claude/commands/continue.md` between "rename stale
sessions" and "orient": for sessions sharing a project's cwd, read enough
of each transcript (and that project's own `docs/todo.md` if present) to
judge whether an older session's task is actually done or superseded by a
newer one — never a mechanical "newest session on this folder wins" rule,
since that would flag legitimate parallel work (verified against root's
own session list: `2. SOPS` had 5 concurrent sessions on different tasks).
Only sessions judged superseded get proposed one at a time;
`archive_session` always requires the user's per-item confirmation
regardless, so this is a detection aid, not an automation.

-----

### 9. Cross-project status report

**Source:** Root hub (hub-native) | **Status:** Available — first run
`docs/reports/status-report-2026-07-17.md`

Tebello asked for a standing way to see every active project's status,
target goal, and open decisions in one place to prioritize/plan against,
rather than reconstructing it from memory each time. Process to regenerate
on request (not automated/scheduled unless Tebello asks for that
separately):

1. For each project in the root `CLAUDE.md` project index that's actually
   active (skip data-only folders and anything excluded like
   `Inventory Management & Reports`, per ADR-004): read its `docs/todo.md`
   (or `1_Documentation/USER_GUIDE.md` execution log for lightweight
   pipeline projects onboarded under ADR-003) for current state and next
   task, plus `git log -1` / `git status` for recency and uncommitted work.
2. For pipeline projects, also check `3_Live_Reports/` file timestamps —
   a stale output file is a stronger staleness signal than anything in the
   docs (proved useful: caught `8. AvgMovement` not having produced a
   report since 2026-05-13, which no todo.md/session-log would have shown
   since those projects don't keep one).
3. Build a table: project | status (🟢/🟡/🔴) | target goal | current
   state, plus a Decisions Needed section and an "other things worth
   looking at" section for anything surfaced during the pass that isn't a
   clean per-project status line (recurring ops friction, hub backlog
   items, etc.).
4. Save the dated report to `docs/reports/status-report-<date>.md` at hub
   root — every project's own report data stays in that project's own
   `docs/todo.md`, this file is just the rollup.

-----

### 10. Shared-core distribution via plain read instruction, not `@import`

**Source:** Root hub (hub-native) | **Status:** Available — pilot in
progress, see `docs/decisions/ADR-007-shared-core-claude-md-template.md`

Claude Code's `@path` import does **not** resolve absolute paths outside the
project tree (confirmed 2026-07-18 — a marker file at
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
never appeared in a fresh session's `claudeMd` block despite a live
`@~/...` import line in root `CLAUDE.md`). Only in-project relative imports
are proven (this hub's own `@docs/patterns.md`). For content that needs to
live in one place outside any single project's tree and reach multiple
projects/machines without per-update edits, use a **plain prose instruction**
instead: the project's `CLAUDE.md` tells Claude to read the external file at
session start and treat its contents as operating instructions. This is not
a language feature — it depends on the session actually complying — but
that's the same self-monitored trust model this hub already accepts for the
context-budget policy ([[ADR-005]]) and session-archival check. Reuse this
pattern for any future case where a genuine `@import` is wanted but doesn't
resolve, before reaching for OS-level workarounds (symlinks were considered
for this same case and rejected — needs Developer Mode/admin rights on
Windows, too fragile across machines).

-----

### 11. Concurrent-session git contamination in a shared working tree (anti-pattern + mitigation)

**Source:** `2. SOPS` (three parallel print/edit sessions, 2026-07-23) |
**Status:** Proven (observed live, independently flagged by all three
sessions)

When multiple Claude Code sessions work the **same git repo in the same
working tree** at once, any session that runs `git add -A` / `git add .`
sweeps up **other** sessions' uncommitted, in-progress files into its own
commit. Observed concretely: one session's `routes/stock_orders.py` +
`tests/test_stock_orders.py` (part of an editable FM/Job-No. feature) were
hoovered into a *different* session's "consolidate matching item lines"
commit (`dca9ee4`), splitting one feature across two commits (`dca9ee4` +
`229e346`) with no clean boundary. Nothing was lost and the split was made
traceable (documented in both commit messages + the project todo), but the
history is messier than one-task-one-commit intends.

**Root cause:** the sessions shared one working tree. This is exactly the
failure mode pattern § 5 (one task = one atomic commit **via git worktrees**)
exists to prevent — each worktree is a separate checkout, so parallel
sessions can't see or stage each other's files. These SOPS sessions weren't
using worktrees.

**Mitigation, in order of preference:**
1. **Structural:** run parallel sessions in separate git worktrees (§ 5) —
   removes the shared tree entirely. Best fix when the parallelism is planned
   (e.g. Executor fan-out).
2. **Behavioral (when worktrees aren't in play):** stage **surgically** —
   `git add <explicit paths>` or hunk-level `git add -p`, never `git add -A`/
   `.` — whenever another session might have uncommitted work in the same
   tree. Stagger commits rather than committing simultaneously.
3. **Traceability (when a collision already happened):** document the split
   in the commit message + todo so the history is explainable, not
   mysterious — don't rewrite history to "fix" it unless asked.

A memory about this hazard was saved during the SOPS session so future
sessions default to surgical staging. Promote to a project's own `CLAUDE.md`
§ hard rules if a repo routinely has concurrent sessions (SOPS is the
current candidate — it regularly has several open at once).

-----

## Not yet promoted (seen once, watch for a second occurrence)

- Domain-tagged session resume (🔴 Trading / 🔵 Engineering / 🟢 Software /
  🟡 Hybrid) from SOPS's `/continue` — only makes sense if a second project
  actually spans those same domains. Root's own `/continue` uses
  project-folder identity instead; revisit if that turns out to be the
  wrong axis.
