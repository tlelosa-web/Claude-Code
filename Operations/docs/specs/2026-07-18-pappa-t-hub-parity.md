# Spec — Pappa T hub parity (ADR-008 execution plan)

**Date:** 2026-07-18 | **Owner:** Tebello Lelosa | **Decision record:** `docs/decisions/ADR-008-pappa-t-independent-hub.md`

## Goal

Get `/continue` (and the rest of the hub-and-spoke pattern: session hygiene,
anti-drift `todo.md`, ADR-007 shared-core updates) working on Pappa T's root,
without overwriting any of its existing vault-specific content, and without
force-pushing Operations' own project index onto it.

## Step 0 — Confirm Pappa T's root `CLAUDE.md` content (blocking, needs Tebello)

Not yet seen from this session — only the folder-structure snapshot was
shared. Before writing `HUB-CHECKLIST.md`'s exact wording, need to know
whether Pappa T's root `CLAUDE.md` already has:
1. The ADR-007 `CORE.md` read-instruction (the one-line "at the start of
   every session, read `~/.claude/plugins/marketplaces/tlelosa-claude-
   config/dcoe-roster/CORE.md`..." instruction).
2. Any existing reference to `.claude/commands/continue.md` or a resume
   flow (even a broken/aspirational one — `folder-structure.md`'s
   "Deviations" section already says CLAUDE.md describes hooks/commands as
   "active" when they're actually empty, so this is likely aspirational
   text that needs reconciling, not adding from zero).
3. Hub-and-spoke language distinguishing root governance from
   `TebelloReborn/CLAUDE.md` and `ai-outreach-agency/CLAUDE.md` (both of
   which already have their own project-level brains, per the snapshot).

**Action:** paste the file, or its relevant sections, and this step closes.
Everything below can proceed in parallel/regardless — only the exact
checklist wording depends on this.

## Step 1 — Add `hub-template/` to `tlelosa-claude-config`

In the local clone at `~/.claude/plugins/marketplaces/tlelosa-claude-config/`:

1. `hub-template/continue.md` — copy of this hub's
   `.claude/commands/continue.md` **verbatim**. Confirmed vault-agnostic:
   no Operations-specific project names, folder paths, or assumptions
   baked in — it operates purely on `list_sessions`, `docs/todo.md`,
   `docs/session-log.md`, and whatever project folders a session finds.
2. `hub-template/HUB-CHECKLIST.md` — new file, short. Lists what a hub
   root's own `CLAUDE.md` needs (not a full template to overwrite with):
   - The ADR-007 `CORE.md` read-instruction line.
   - A pointer to `.claude/commands/continue.md` existing and being the
     session-resume entry point.
   - A "Hard Rules" section that doesn't contradict `CORE.md`'s universal
     rules (it can add local ones, never relax the shared ones — same
     rule Operations' own `CLAUDE.md` follows).
   - A note that project-level `CLAUDE.md`s (any sub-project with its own
     brain) take precedence over the hub root for work inside that
     project's folder — the hub-and-spoke rule, generalized.
3. `README.md` (repo root, existing file) — add a short pointer to
   `hub-template/` alongside the existing project-level
   `CLAUDE.md.template` section, so the repo's own README explains both
   tiers exist.

**Gate:** same as the `CORE.md` push — this is a shared repo both machines
pull from. Get Tebello's explicit sign-off before pushing, matching the
precedent set when `CORE.md` was first pushed.

## Step 2 — Apply on Pappa T (Tebello or a session running there — not this session)

This session runs on the Fan Movement work PC and cannot write files to
Pappa T. Concrete steps for whoever runs this on that machine:

1. `/plugin marketplace update tlelosa-claude-config` (pulls `hub-template/`
   down via the existing marketplace clone).
2. Copy `~/.claude/plugins/marketplaces/tlelosa-claude-config/hub-template/
   continue.md` → `Pappa T/.claude/commands/continue.md`.
3. Open Pappa T's root `CLAUDE.md`, reconcile against
   `hub-template/HUB-CHECKLIST.md` — add whatever's missing, don't
   restructure what's already there.
4. Sanity-check: open a **fresh** session at the Pappa T vault root, run
   `/continue`, confirm it now produces a real resume report instead of
   "command not found" or silence — same verification discipline ADR-007
   used for `CORE.md` (a fresh session is the only valid test).

## Explicitly out of scope here

The hygiene deviations already flagged in Pappa T's own
`docs/folder-structure.md` (`TebelloReborn`'s forked agent roster, the
untracked nested `Tenders/4_Scripts/tenders-sa/` git project, `.Codex/` vs
`.claude/` coexistence) — real findings, but separate from making
`/continue` work. Worth their own follow-up once this lands, Tebello's
call on priority.

## Verification — DONE

- Fresh session at Pappa T root: `/continue` runs and produces a resume
  report grounded in Pappa T's actual `docs/todo.md`/`session-log.md`
  content (not Operations' — a wrong-content result would mean the copy
  went to the wrong project's `.claude/commands/`, not the vault root).
  **Confirmed by Tebello 2026-07-18: "continue works."**
- `docs/todo.md` here gets a closing entry once Step 2's fresh-session
  check is confirmed back to this hub (same handoff-verification pattern
  as ADR-007). Done — see `docs/todo.md` Done section.
