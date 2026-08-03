# ADR-002 — Roll out DCOE to all remaining projects

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

ADR-001 deliberately deferred onboarding any of the five non-SOPS projects
to DCOE until there was a concrete reason to prioritize one over another
(`docs/todo.md` backlog: "ask Tebello what the concrete near-term goals are
for each active project"). Asked directly during the hub-setup completion
session (2026-07-15); Tebello's answer was to onboard **all** of them,
rather than pick one.

Candidates: `7. DELIVERY NOTE` (Next.js, has its own CLAUDE.md/AGENTS.md but
not DCOE-aligned), `1. Daily Sales Order Files`, `8. AvgMovement`,
`Inventory Management & Reports` (three Python pipeline projects sharing the
`1_Documentation/`→`5_Archive_and_Debug/` folder convention — see
`docs/patterns.md` § 6), and `3. Nameplate & Test Sheet` (full-stack, own
git repo, no CLAUDE.md/AGENTS.md yet).

## Decision

1. **All five projects will be onboarded to DCOE** — this is the standing
   direction, not a per-project decision to re-litigate each time. Hub
   `CLAUDE.md` hard rule 6 ("no project onboards without a deliberate
   decision") is satisfied by this ADR at the batch level; per-project
   onboarding sessions still each get their own Domain-agent scope
   confirmation before building, since stack and constraints differ.
2. **Sequencing is not "all at once."** Each onboarding is its own planning
   task (new `CLAUDE.md`, `docs/` scaffold, possibly a spec for anything
   non-trivial in that project's stack) — treated as separate hub-level
   tasks in `docs/todo.md`, not a single mega-task.
3. **The three pipeline projects share a prerequisite.** Before any of
   `1. Daily Sales Order Files`, `8. AvgMovement`, or
   `Inventory Management & Reports` onboards, the pipeline-folder
   convention must be reconciled with DCOE's `docs/specs/`+`docs/todo.md`
   convention (`docs/patterns.md` § 6) — doing this once, generically, on
   whichever pipeline project onboards first, then reusing the answer for
   the other two rather than re-deciding per project.
4. **No fixed order was specified.** Absent an explicit priority, default
   sequencing is: whichever project has the next concrete piece of work
   land first gets onboarded as part of that work (consistent with ADR-001's
   original "concrete task" trigger, now applied per-project instead of
   gating the whole rollout).

## Consequences

- `docs/todo.md` § Next up gets five new per-project onboarding tasks
  instead of one open "decide rollout order" item.
- The pipeline-convention reconciliation (previously blocked pending a
  rollout order) is now unblocked — it happens on the first pipeline
  project touched, not deferred indefinitely.
- Five projects picking up DCOE conventions independently means five
  separate CLAUDE.md files to keep from drifting on shared policy (model
  routing, agent roster) — same mitigation as ADR-001: point to a shared
  policy source (root `CLAUDE.md`/SOPS's model-routing section) rather than
  duplicating it in each.
