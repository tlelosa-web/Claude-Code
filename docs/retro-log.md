# retro-log.md — Claude-Code hub

Marker file for `/retro` (`.claude/commands/retro.md`). Each run appends one
entry; Step 1 of the next run reads only `session-log.md` entries **after** the
most recent marker below. Without this file `/retro` would re-propose patterns
already raised and already answered.

**Contention file.** This is the hub's fourth, alongside `docs/todo.md`,
`docs/session-log.md` and `knowledge/INDEX.md` — see `CLAUDE.md` Hard Rule 6.
`git fetch origin` + `git pull origin main` immediately before appending. On a
conflict, resolve as a real union of both runs' entries; never keep one and drop
the other.

Most recent last, matching `docs/session-log.md`'s convention.

-----

## 2026-08-10 — /retro run
Reviewed: session-log entries 2026-07-28 → 2026-08-10 (all 47 — first run, unbounded per Step 1, no prior marker) | todo.md as of 2026-08-10
Proposed: 6 items — 6 selected, 0 deferred
Selected:
1. `CORE.md` hard rule — a record is not a control (universal, spec required)
2. `/session-end` Step 1.5 per-repo rather than per-session (universal)
3. Done entries must cite a SHA on `main` (universal)
4. Roster delivery to cloud sessions (universal, spec required)
5. Stop writing counts as prose (this hub)
6. Promote or park items recited in "Known risks" (this hub)

Universal items 1-4 queued in `tlelosa-claude-config/docs/todo.md` per ADR-008;
hub items 5-6 in this repo's `docs/todo.md`. Nothing built — Step 4 queues.

Held back (single-entry evidence, not proposed): the `/session-end` Step-N
cross-reference off-by-one that survived to 2026-08-09, and
`CLAUDE.md.template`'s unverified "introductory pricing ends 31 August 2026"
claim, which is already an open config-repo item.

Note for the next run: this run was itself triggered inside the session that
had to *land* `/retro` from a stranded branch, so its evidence window includes
the failure that delayed it. Item 1 is the pattern the log had already
diagnosed four times without installing a control — if it recurs after being
queued here, that is itself the strongest possible argument for the rule.

-----

## 2026-08-20 — /retro run
Reviewed: session-log entries 2026-08-12 → 2026-08-20 (5 entries, bounded per
the 2026-08-10 marker) | todo.md as of 2026-08-20
Proposed: 3 items — 3 selected, 0 deferred
Selected:
1. Moved-repo topic files get a top-of-file banner, not just an `INDEX.md`
   row (this hub) — implemented same session, `knowledge/pitwall-companion.md`
2. Strengthen `CORE.md` Hard Rule 10 — verify the fetch itself succeeded, not
   just that one was run (universal, spec required)
3. Cross-project knowledge-cache checklist item in close-out commands
   (universal, spec required)

Item 1 landed directly (single-file, under the plan-first threshold).
Universal items 2-3 queued in `tlelosa-claude-config/docs/todo.md` per
ADR-008, since they change shared core / `hub-template/`. Nothing else
built this run.

Held back (single-entry evidence, not proposed): a direct push to this hub
bypassed a PR-required branch-protection rule (noted once, 2026-08-12) —
worth knowing, not yet a pattern.

Note for the next run: items 2 and 3 both trace back to the same shape as
last run's item 1 ("a record is not a control") — a lesson was written down
in a session log and never installed. Worth watching whether the *pattern of
finding "record not control" instances* is itself now the dominant recurring
friction, which would argue for a stronger structural fix (e.g. a
`/session-end` step that greps recent entries for un-actioned "worth a
`/retro` candidate"-style language) rather than fixing each instance
one at a time.
