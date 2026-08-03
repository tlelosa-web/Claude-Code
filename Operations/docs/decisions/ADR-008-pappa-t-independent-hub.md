# ADR-008 — Pappa T as an independent hub root, using the ADR-007 channel

**Date:** 2026-07-18
**Status:** Accepted — applied and verified on Pappa T (Tebello confirmed
`/continue` works there as of 2026-07-18).
**Owner:** Tebello Lelosa

## Context

Tebello wants his personal "Pappa T" vault (home PC) to run under the same
hub-and-spoke DCOE governance as this `Operations` hub — same `/continue`
resume flow, same session hygiene, same shared-core distribution (ADR-007)
— with entirely different content: Pappa T is a life-domain vault (numbered
`00_Index_&_Logs/` … `05_Archive/` folders, `docs/life-domains.md`,
`docs/strengths-inventory.md`, etc.) plus several actual coding projects
(`MIMS App`, `IQ`, `TebelloReborn`, `Tenders`, `ai-outreach-agency`), not a
company project-folder index like Operations'.

**Immediate trigger:** Tebello reported `/continue` "not working" on Pappa
T. A folder-structure snapshot he provided (`docs/folder-structure.md` on
that vault, dated 2026-07-18) confirms the root cause: Pappa T's root
`.claude/commands/` is empty (`.gitkeep` only) — no `/continue` was ever
wired up at the vault root. The only working `/continue` on that machine
lives inside `ai-outreach-agency/`, a sub-project, not the root.

This is **not** a from-scratch hub build. Pappa T's root already has real
DCOE scaffolding: `CLAUDE.md`, `AGENTS.md`, `docs/` (`architecture.md`,
`api-patterns.md`, `code-conventions.md`, `domain-brief.md`,
`life-domains.md`, `orchestration-model.md`, `project-portfolio.md`,
`session-log.md`, `todo.md`, `decisions/ADR-001-dcoe-vault-structure.md`),
and a `.Codex/agents/` roster (19 files — the 9-role DCOE roster plus 10
life-domain specialists: career-brand, finance-risk, identity-strengths,
learning-capability, operations-systems, strategy-governance,
tender-opportunities, venture-builder, wellbeing-rhythm). It's a partially
completed hub, missing the one piece that makes `/continue` work, plus
(per that vault's own `folder-structure.md` "Deviations" section) a few
known hygiene gaps unrelated to this ADR.

**Not yet seen:** the actual content of Pappa T's root `CLAUDE.md` — only
its existence and the folder snapshot were shared in chat. This ADR can't
confirm whether it already carries the ADR-007 `CORE.md` read-instruction,
or references `.claude/commands/continue.md` at all. That's a blocking
unknown for exact execution (see spec's Step 0), not for the mechanism
decision below.

## Decision

1. **Reuse the ADR-007 channel, don't invent a new one.** The
   `tlelosa-claude-config` repo already solves "how does content reach
   both machines" for `CORE.md`. Extend it with a `hub-template/` folder
   carrying the parts of a hub root that are genuinely reusable across
   *any* Tebello-governed vault, not just Operations:
   - `hub-template/continue.md` — the `/continue` command itself. Already
     vault-content-agnostic (it reads `docs/todo.md`/`docs/session-log.md`
     generically, does session hygiene via `list_sessions`, and defers to
     whatever project folders it finds — nothing Operations-specific is
     hardcoded in it). Copy as-is into any hub root's
     `.claude/commands/continue.md`.
   - `hub-template/HUB-CHECKLIST.md` — not a CLAUDE.md to overwrite (Pappa
     T's root `CLAUDE.md` already has real, vault-specific content that a
     master-file overwrite would destroy — same reasoning ADR-007 already
     established for project-level files), but a short checklist of what a
     hub root's own `CLAUDE.md` needs to *contain* to run this pattern:
     the `CORE.md` read-instruction line, a pointer to
     `.claude/commands/continue.md`, and the hub-and-spoke framing (root
     brain vs. sub-project brains). A session on any machine reconciles its
     own `CLAUDE.md` against this checklist rather than having it forced.
2. **Hub-root content stays local, per hub — same "shared core only"
   principle as ADR-007.** Pappa T's project index (its actual life
   domains and coding projects) is never written into the shared repo —
   only the mechanical skeleton (`continue.md`, the checklist) is shared.
   This is the first time that "shared core" principle is applied one
   level up (hub-to-hub) instead of project-to-project, but it's the same
   rule, not a new one.
3. **Rollout is a deliberate, one-time application on Pappa T**, not
   automatic. Applying the template there requires a session actually
   running on that machine (this session, on the Fan Movement work PC,
   cannot write files to Pappa T). Tebello runs `/plugin marketplace
   update tlelosa-claude-config` there, then a session copies
   `hub-template/continue.md` into place and reconciles `CLAUDE.md`
   against `HUB-CHECKLIST.md`.
4. **Out of scope for this ADR** (flagged, not actioned here): the
   hygiene deviations Pappa T's own `folder-structure.md` already lists —
   `TebelloReborn/.claude/agents/` forking the full roster instead of
   overriding, `Tenders/4_Scripts/tenders-sa/` being an untracked nested
   git project, and the `.Codex/` vs `.claude/` coexistence (also seen in
   `2. SOPS` — worth a `docs/patterns.md` entry once it's confirmed as a
   recurring, deliberate pattern rather than leftover scaffolding). These
   are Pappa T's own backlog items, not blockers for getting `/continue`
   working.

## Consequences

- Once applied, Pappa T gets the same `/continue` resume flow, session
  hygiene (Step 0/0.5), and shared-core update check (Step 1.5) as
  Operations — but its own `docs/todo.md`, `docs/session-log.md`, and
  project index stay entirely its own content.
- `tlelosa-claude-config` now distributes two tiers of shared content:
  project-level (`CLAUDE.md.template`, pre-existing) and hub-level (new
  `hub-template/`). Both stay "mechanism only," never prescribing project-
  or vault-specific content — consistent with the repo's own README
  ("never project content or company data").
- If a third hub root is ever needed (a new machine, or splitting Pappa T
  further), the same `hub-template/` is the install source — this ADR is
  written generically enough to not be Pappa-T-specific in mechanism, only
  in this particular rollout's target.

See `docs/specs/2026-07-18-pappa-t-hub-parity.md` for the execution plan.

## Addendum — 2026-08-03: "separate machine" premise superseded

The Context and Decision above frame this as governance parity between two
vaults on **different physical machines** ("Operations... Fan Movement work
PC" vs. "Pappa T... home PC"). That premise no longer holds: the Operations
tree was migrated onto the same physical machine as Pappa T on 2026-08-03
(see this hub's own `docs/session-log.md` and `docs/todo.md` § Done for that
date). Both vaults are now sibling folders under one Windows user profile
(`tlelo`) — `C:\Users\tlelo\Desktop\Operations` and
`C:\Users\tlelo\Desktop\Pappa T`.

**What still holds:** the shared-core distribution mechanism itself (§
Decision points 1–2 — `hub-template/` in `tlelosa-claude-config`, "shared
core only, never full-file overwrite") is unaffected by machine identity. It
was designed to work over a shared *git remote*, not a shared *disk*, so it
still applies even now that a disk-level shortcut would technically work
too — no reason to unwind it.

**What changed in practice:** since both hubs share one Windows user
profile, they also now share one `~/.claude` — user-scope plugin installs
(`dcoe-roster`, `shared-skills`) and the local `tlelosa-claude-config`
marketplace clone are literally the same files for both vaults, not two
independently-synced copies. A plugin update pulled from either hub's
session is immediately visible to the other. Session-listing tools
(`list_sessions`/`list_events`) also now return both vaults' sessions
together, which matters for `/continue`'s Step 0/0.5 grouping-by-`cwd` logic
in both hubs' `.claude/commands/continue.md`.
Pappa T's own `CLAUDE.md` was updated the same day (2026-08-03, from an
Operations-side session with direct file access to that vault) to note the
merge — see that file's Project Overview section.

**Not reopened:** rollout scope (§ Decision point 3, "one-time application
on Pappa T") and out-of-scope items (§ Decision point 4) are unaffected —
this addendum only corrects the machine-identity framing, not the ADR's
actual decisions.
