# ADR-001 — Hub-and-spoke DCOE at Operations root

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

`2. SOPS` already runs a mature DCOE workflow (v3.2 brain: Domain → Context
→ Orchestrate → Execute), with its own `CLAUDE.md`, `docs/`, agent roster,
and permission rules. The rest of the Operations folder (5+ other active
projects) either has no AI-workflow brain or uses older, ad-hoc
`AGENT.md`/`GEMINI.md` files. The root `Operations/` folder itself had no
brain at all — just a stray, effectively empty `.claude/settings.local.json`.

Tebello wants Operations root set up as the place we work together going
forward, following the DCOE framework.

## Decision

1. **Hub-and-spoke, not unification.** Root gets its own lightweight DCOE
   brain (`CLAUDE.md`) that governs cross-project decisions and root-level
   work. It does not replace or override SOPS's (or any project's) own
   brain — those remain authoritative for work inside that project's
   folder.
2. **The hub brain must be able to grow.** Rather than being a static
   index, root `CLAUDE.md` delegates to `docs/patterns.md` — a living
   registry of workflow patterns proven in individual projects, promoted
   upward once reusable. This is the explicit mechanism for the hub to
   "develop from skills & tools picked up in other projects," per
   Tebello's stated requirement.
3. **Base version: SOPS v3.2**, generalized (stack-specific sections
   dropped or referenced-not-duplicated, to avoid the two brains drifting
   out of sync on shared policy like model routing).
4. **No project onboarding as a side effect.** Bringing another project
   (Delivery Note, Daily Sales Order, AvgMovement, Inventory Management,
   Nameplate & Test Sheet) onto DCOE is deferred until there's a concrete
   task there worth planning properly — not done wholesale now.
5. **Root stays outside git**, deliberately, until the known OneDrive/git
   corruption risk (already observed in SOPS's own repo) is addressed.

## Consequences

- Two DCOE brains now exist (root + SOPS) with policy that could drift.
  Mitigated by root `CLAUDE.md` explicitly pointing to SOPS's brain for
  shared policy (e.g. model routing) rather than re-stating it.
- Other projects remain on inconsistent/legacy workflow conventions
  (`AGENT.md`, pipeline folder layout) until deliberately migrated — this
  is accepted short-term inconsistency in exchange for not disrupting
  working projects.
- The OneDrive/git risk remains unresolved for now; tracked in
  `docs/todo.md` as the next task after this setup.
