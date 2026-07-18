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

- [ ] Trim `CLAUDE.md` back under its 500-line target (currently ~518 lines
      — the DCOE diagram and model-routing table are duplicated internally
      and now also duplicate `CORE.md`)
- [ ] Clean up `TebelloReborn/.claude/agents/` — delete the full 9-agent
      roster fork, keep only genuine per-agent overrides (known violation,
      flagged in `CLAUDE.md`, left in place deliberately until addressed)
- [ ] Resolve `Tenders/4_Scripts/tenders-sa/` — untracked nested git repo;
      decide whether to add as a proper git submodule or drop it from this
      repo entirely
- [ ] Pull 2 pending upstream commits into the shared CORE.md template:
      `/plugin marketplace update tlelosa-claude-config`

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
