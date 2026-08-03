# ADR-007 — Shared-core CLAUDE.md template, distributed via the plugin marketplace

**Date:** 2026-07-18 (mechanism revised same day after Step 0 verification)
**Status:** Accepted — pivoted from `@import` to a plain read-instruction
mechanism after Step 0 disproved the import assumption; rollout proceeding
per the revised spec.
**Owner:** Tebello Lelosa

## Context

Tebello runs Claude Code on two machines (the Fan Movement work PC, this
`Operations` tree, and his personal "Pappa T" home PC) and across several
independently-governed projects (root hub, `2. SOPS`, `7. DELIVERY NOTE`,
`3. Nameplate & Test Sheet`, the pipeline projects). Each has its own
`CLAUDE.md`, and each has independently drifted in version: SOPS and the
`tlelosa-claude-config` repo's `CLAUDE.md.template` are both v3.2; the root
hub is v1.0 "based on" that but generalized; other projects have their own
histories.

Tebello asked for the `tlelosa-claude-config` repo's `CLAUDE.md.template` to
become **the master file used on all current and future projects**, with
learnings from either machine flowing back into it, and new versions
"deployed on each commit."

Read literally, "master file for all projects" collides with a rule already
recorded in this hub's own `CLAUDE.md` (§ Hub-and-Spoke Rule, itself
ADR-001): *"Patterns flow upward, not down... adopted by other projects
deliberately — never force-pushed onto them."* Every project's `CLAUDE.md`
today also carries real, project-specific content (stack, folder layout,
project hard rules) that a full-file overwrite would destroy.

Two scoping questions were put to Tebello directly and answered:

1. **What does the template master** — the whole file, or just the
   shared/reusable parts? → **Shared core only.** The DCOE pattern,
   sub-agent roster, model routing, and genuinely universal hard rules move
   into a shared file; each project keeps its own stack/folder-structure/
   project-specific-rules content locally, untouched.
2. **What does "deployed on each commit" mean mechanically?** →
   **Automated notify, manual apply.** A commit to the shared file should
   surface as a signal that an update is available; a human still approves
   before it lands anywhere. Not a CI job that silently overwrites project
   files.

This resolves the apparent conflict with ADR-001 rather than reversing it:
adoption of an updated shared core is still a deliberate act by a human (or
a session Tebello is driving), just through a purpose-built channel instead
of ad hoc copy-paste discovery.

### Technical mechanism found

The `dcoe-roster` plugin marketplace (already installed on this machine, see
[[reference_dcoe_roster_marketplace]]) maintains a real local git clone of
`tlelosa-claude-config` at a fixed, machine-local path:

```
~/.claude/plugins/marketplaces/tlelosa-claude-config/
```

(Confirmed present at `C:\Users\Fan Movement\.claude\plugins\marketplaces\
tlelosa-claude-config\` on this machine, containing `CLAUDE.md.template`,
`dcoe-roster/`, and `README.md` as tracked files.) This clone is refreshed
via `/plugin marketplace update tlelosa-claude-config` (manual) or an
optional background refresh if a `GITHUB_TOKEN` is set (per the repo's own
README). Claude Code's `@path` import syntax in `CLAUDE.md` already works
for in-project relative paths (this hub's own `CLAUDE.md` imports
`@docs/patterns.md` today). This ADR originally assumed `@~/...` absolute
imports outside the project tree would also work — **Step 0 of the linked
spec disproved this on 2026-07-18**: a marker string placed in a throwaway
local `CORE.md` never appeared in a fresh session's `claudeMd` system-reminder
block despite the import line being live in root `CLAUDE.md` at the time. The
probe was reverted.

**Revised mechanism:** since Claude Code will not auto-resolve the absolute
path, the shared file is instead surfaced via a **plain read instruction** —
each opted-in project's own `CLAUDE.md` tells Claude in prose to read
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
at session start and treat its contents as live operating instructions. This
is not a Claude Code feature, just an instruction a session follows — same
self-monitored trust model this hub already relies on for the context-budget
policy (ADR-005). It keeps the property Tebello actually wanted (no
per-project file edit needed when `CORE.md`'s *content* changes — only the
one-time opt-in edit), without depending on import resolution or on Windows
symlinks (considered and rejected: needs Developer Mode or admin rights on
both machines, too fragile for a two-machine setup).

## Decision

1. A new file, `dcoe-roster/CORE.md`, is added to the `tlelosa-claude-config`
   repo. It carries the shared/reusable sections only: DCOE pattern
   description, sub-agent roster + model routing table, and hard rules that
   are genuinely universal across every project (not project-specific ones
   like SOPS's "offline-first always" or a pipeline project's "folders are
   load-bearing"). It carries its own `Core version: X.Y` line, independent
   of any single project's own CLAUDE.md version number.
2. Projects that opt in add one short read-instruction near the top of their
   own `CLAUDE.md`, e.g.: *"At the start of every session, read
   `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
   and treat its contents as part of this project's operating instructions."*
   Nothing else in that project's `CLAUDE.md` changes. This is a one-time,
   per-project edit — not repeated per update.
3. Once the instruction exists, **every future core update reaches that
   project the next time a session actually reads the file** — no further
   per-project file edits are ever needed for core-content changes.
   "Deploying a new version" is: edit `CORE.md` in the repo → commit → push
   → (on each machine) `/plugin marketplace update tlelosa-claude-config`.
   Unlike a true `@import`, this depends on the session actually following
   the instruction — the same trust model as every other self-monitored
   `CLAUDE.md` rule (e.g. ADR-005's context-budget threshold), not a new
   category of risk.
4. **Notify mechanism**: a lightweight check (`git fetch` + compare local
   `HEAD` to `origin/main` in the marketplace clone) surfaces "N new core
   commits available, run `/plugin marketplace update`" during normal
   session-start orientation (hub `/continue`, and per-project `/continue`
   for any project that has opted in). This is a signal, not an action —
   pulling the update is still Tebello's call.
5. **Rollout is per-project and deliberate**, consistent with ADR-001: the
   root hub adopts the import first, as the pilot (lowest risk — no other
   project's governance is affected by editing the hub's own file). Each
   sub-project (SOPS, DELIVERY NOTE, Nameplate, pipeline projects) opts in
   only when that project is next actually being worked on, same trigger
   pattern as the original DCOE rollout (ADR-002) — not force-pushed onto
   all of them today as a side effect of this ADR.
6. **Learnings flow back**: when something proven in one project's own
   `CLAUDE.md` turns out to be genuinely universal (not project-specific),
   it gets promoted into `CORE.md` in the repo — same "patterns flow
   upward, promoted deliberately" spirit as `docs/patterns.md` already
   documents, just landing in the shared file instead of (or in addition
   to) the hub's pattern library.

## Consequences

- `docs/patterns.md` § 4 ("User-level agent roster") and the hub
  `CLAUDE.md` § Sub-agent roster section become largely redundant with
  `CORE.md` once the hub adopts the import — they should be trimmed to a
  pointer once the pilot is verified working, not left duplicated
  indefinitely.
- Every project that opts in gains a live dependency on
  `~/.claude/plugins/marketplaces/tlelosa-claude-config/` existing and
  being reasonably current on whichever machine a session runs on. If that
  marketplace isn't installed on a given machine (a fresh machine, or one
  where install failed), the read instruction will fail visibly — a session
  that tries to read the file gets a file-not-found error it can report,
  not a silent gap — verified during the pilot.
- This does **not** change hub `CLAUDE.md` hard rule 1 ("this root brain
  never overrides a sub-project's own CLAUDE.md/AGENTS.md for work done
  inside that project's folder") — adding the read instruction to a
  sub-project's `CLAUDE.md` is still that project's own deliberate act, not
  something imposed by root.
- The mechanism now depends on a session actually following a prose
  instruction rather than on a Claude Code language feature — a softer
  guarantee than a working `@import` would have been, but consistent with
  every other self-monitored policy already in this hub's `CLAUDE.md`
  (context budget, session archival). Revisit if this ever proves
  unreliable in practice (e.g. a session repeatedly forgets to read it).

See `docs/specs/2026-07-18-shared-core-claude-md-template.md` for the
execution plan, including the verification step.
