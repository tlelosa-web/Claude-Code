# Spec — Shared-core CLAUDE.md template rollout

**Date:** 2026-07-18 | **Decision record:** `docs/decisions/ADR-007-shared-
core-claude-md-template.md` | **Status:** Step 0 complete (failed as
originally designed, mechanism revised). Steps 1–2 in progress this session.

## Goal

Make the reusable parts of `CLAUDE.md` (DCOE pattern, sub-agent roster,
model routing, universal hard rules) live in exactly one place —
`tlelosa-claude-config`'s `dcoe-roster/CORE.md` — so a change made from
either machine (Operations/work PC or Pappa T/home PC) reaches every
opted-in project without hand-copying, while every project keeps its own
stack-specific content local and update adoption stays a deliberate,
visible human decision (not silent auto-overwrite).

## Step 0 — Verify the technical assumption (blocking, do this before anything else) — DONE, FAILED

The whole design depended on Claude Code's `@path` import resolving an
absolute path outside the project tree (`~/.claude/plugins/marketplaces/
tlelosa-claude-config/dcoe-roster/CORE.md`), not just in-project relative
imports (which are already proven — this hub's own `CLAUDE.md` successfully
imports `@docs/patterns.md` today).

1. Added a throwaway `dcoe-roster/CORE.md` to a **local-only**, untracked file
   in the marketplace clone at `~/.claude/plugins/marketplaces/tlelosa-claude-
   config/` (never pushed to GitHub) with an obvious marker string,
   `<!-- CORE-IMPORT-TEST-2026-07-18 -->`.
2. Added one line near the top of the **root hub's own** `CLAUDE.md`:
   `@~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/
   CORE.md`
3. Started a **fresh** Claude Code session at `C:\Dev\Operations` and checked
   for the marker string in the session's system-reminder `claudeMd` block.
4. **Result: it does not work.** The marker was never present. Both probe
   changes were reverted (hub `CLAUDE.md` import line + temp comment
   removed). Per ADR-007's revised Decision, the mechanism pivoted to a
   **plain read instruction** instead of `@import` — Tebello confirmed this
   as the preferred approach (over a Windows-symlink workaround or a manual
   sync/copy script) on 2026-07-18. Steps 1–4 below are rewritten for that
   mechanism.

## Step 1 — Build `CORE.md` (in the real repo)

Source material: `CLAUDE.md.template` (repo) and the hub's own `CLAUDE.md`
§ Sub-agent roster / § DCOE Agent Architecture, which are currently the two
most-authoritative copies of this content and have already drifted slightly
(e.g. hub's roster table has no `Default file` column; the template's does).

Contents of `CORE.md`:
- DCOE pattern description + the 4-stage diagram (Domain → Context →
  Orchestrate → Execute)
- Sub-agent roster table (9 agents) + model routing table (Sonnet 5
  default, Opus escalation-only, standing reviewer exception)
- Hard rules that are genuinely universal (not project-specific) — e.g.
  "no code without a plan for >2 files," "opus is earned, not assigned,"
  "if acceptance criteria are unclear, stop and ask," "ask before deleting
  production data"
- A `Core version: X.Y` line at the top, versioned independently of any
  single project's own `CLAUDE.md` version number
- Explicitly **excluded**: anything stack-specific, folder-layout-specific,
  or project-specific (those stay local to each project's own `CLAUDE.md`)

Built at `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/
CORE.md` (Core version 1.0), replacing the Step-0 test-marker content.
**Still pending:** commit and push to `tlelosa-claude-config`'s real remote —
ask Tebello before pushing (this is a shared repo touched from multiple
machines).

## Step 2 — Pilot: root hub adopts the read instruction

1. Add a short read-instruction near the top of `C:\Dev\Operations\CLAUDE.md`:
   *"At the start of every session, read
   `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
   and treat its contents as part of this hub's operating instructions."*
2. Trim the now-duplicated sections (§ Sub-agent roster, § DCOE Agent
   Architecture) down to a short pointer at the read instruction, keeping
   only what's genuinely hub-specific (the project index, the hub-and-spoke
   rule itself, hub hard rules).
3. Verify in a fresh session that the resulting `CLAUDE.md` still reads
   correctly and Claude actually reads and applies `CORE.md`'s content when
   instructed (this is the equivalent proof step to Step 0, but for a prose
   instruction rather than a language feature — lower risk, but still worth
   a real check rather than assuming compliance).
4. Update `docs/patterns.md` § 4 to note the roster now flows through
   `CORE.md` rather than being independently deployed at
   `~/.claude/agents/` — reconcile which is actually authoritative if both
   still exist (the plugin install may render the standalone
   `~/.claude/agents/*.md` files redundant; confirm before deleting
   anything there, since other machines/sessions may still depend on them).

## Step 3 — Notify mechanism

Add one step to `.claude/commands/continue.md` (hub's own, then each
project's own copy as it opts in), between the existing session-start
checks:

```
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config fetch --quiet
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config rev-list HEAD..origin/main --count
```

If the count is > 0, surface in the resume report: "Shared core template
has N new commit(s) upstream — run `/plugin marketplace update
tlelosa-claude-config` to pull them in." Never run the update
automatically.

## Step 4 — Per-project opt-in (one at a time, on request)

For each of `2. SOPS`, `7. DELIVERY NOTE`, `3. Nameplate & Test Sheet`, the
pipeline projects, and Pappa T's own projects: add the same read instruction
+ trim duplicated sections, **only when that project is next actually being
worked on** — same trigger as the original DCOE rollout (ADR-002). Not a
batch operation done today. Each opt-in is a small, single-file, low-risk
edit once Step 2 has proven the mechanism works.

## Explicitly out of scope for this spec

- Any CI/automated push that edits project files without a human step.
- Migrating Pappa T's actual local files (that machine isn't reachable from
  this session — Tebello runs the equivalent steps there manually, or in a
  session on that machine).
- Deleting or archiving `~/.claude/agents/*.md` — a separate decision once
  Step 2 confirms `CORE.md` is genuinely authoritative and current.
