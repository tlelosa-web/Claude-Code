# Pappa T — Hub Task Queue

> This file previously held `ai-outreach-agency`'s task queue — a leftover
> from when this repo's root *was* that project, before the 2026-07-18 vault
> import restructured it under `ai-outreach-agency/`. That project's live
> queue is now self-governed at `ai-outreach-agency/docs/todo.md`. This file
> tracks hub-level tasks only: cross-project work and anything started at
> the vault root.

## In Progress

_(none — awaiting next task selection)_

## Backlog

_(none — all backlog items from the 2026-07-18 cleanup pass are complete)_

## Completed

- [x] Import Master Vault structure — strategic docs, CVs, sibling projects
      (`8612c8e`)
- [x] Align project with dcoe-roster v3.2 template (`48e13d5`)
- [x] Rename vault to Pappa T, add ai-outreach-agency, flag known drift
      (`39ee392`)
- [x] Add as-is folder-structure snapshot (`c7791c7`)
- [x] Wire up hub-and-spoke pattern — CORE.md read instruction, `/continue`
      command (`5620fd1`)
- [x] Verify `/continue` resumes correctly from a fresh session
- [x] Pull 2 pending upstream commits into the shared CORE.md template
      (`eff87e8` — home PC → Pappa T rename, fast-forwarded into the local
      marketplace clone at `~/.claude/plugins/marketplaces/tlelosa-claude-config`)
- [x] Trim `CLAUDE.md` back under its 500-line target — 519 → 457 lines;
      also corrected the stale `~/.claude/agents/` path reference and
      resolved the TebelloReborn roster note (see next item) (`d7bf782`)
- [x] Investigated the "TebelloReborn roster fork" flag — turned out to be
      a deliberate, fully-tailored override (not a stale copy), sanctioned
      by TebelloReborn's own `CLAUDE.md`. Updated the hub `CLAUDE.md` note
      accordingly instead of deleting the files (`d7bf782`)
- [x] Resolved `Tenders/4_Scripts/tenders-sa/` — registered as a proper git
      submodule pointing at `alfa-rsa/tenders-sa` (`d6da4c3`)
