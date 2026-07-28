# Pappa T — Hub Task Queue

> This file previously held `ai-outreach-agency`'s task queue — a leftover
> from when this repo's root *was* that project, before the 2026-07-18 vault
> import restructured it under `ai-outreach-agency/`. That project's live
> queue is now self-governed at `ai-outreach-agency/docs/todo.md`. This file
> tracks hub-level tasks only: cross-project work and anything started at
> the vault root.

## In Progress

- [ ] **PRIORITY, PAUSED FOR REDESIGN** — `TebelloReborn`: PNet/Careers24 Vacancy Coverage build
      (spec: `TebelloReborn/docs/specs/pnet-careers24-coverage.md`). Phases 9–11 (steps 55–62)
      built and committed; Phase 12+ paused 2026-07-29 — Tebello caught objective drift: the
      spec's static manually-curated seed-URL config contradicts the project's actual goal
      (fully automated vacancy discovery, human review only at the final approval gate).
      Needs a fresh Domain → Planner redesign pass for automated discovery (search-URL
      construction from `SEARCH_TITLES`/`SEARCH_LOCATION`, mirroring Indeed/LinkedIn's
      approach) before build resumes. See `TebelloReborn/docs/todo.md`'s Phase 9–14 section
      for full detail. Still prioritized over the `ai-outreach-agency` items below once
      redesign + build resumes.

## Next up

_(deprioritized until the TebelloReborn item above is up and running — do not start without checking with Tebello first)_

- [ ] Top up OpenRouter credits (openrouter.ai/settings/credits) — `ai-outreach-agency`'s
      `asset_gen` stage has been blocked on HTTP 402 since 2026-07-04; unblocks real
      (non-offline) batch runs until Build Queue A (headless Claude Code migration) lands.
- [ ] `ai-outreach-agency`: bump `research/ollama_client.py`'s `READ_TIMEOUT` 60s → 120s and
      add `"keep_alive": "30m"` to the `/api/generate` payload — local Ollama generation is
      sitting close to the current timeout ceiling on cold-load calls, which risks
      intermittent false-positive `OllamaError`s on an otherwise-healthy daemon during a
      real batch. Small, single-file, RED/GREEN-able in one commit.

## Backlog

- [ ] Propagate the "Codex-review + fold strongest points into spec before build" standard
      procedure (added 2026-07-29 to hub `CLAUDE.md` Pattern 1 and `TebelloReborn/CLAUDE.md`
      Hard Rule #13) to `ai-outreach-agency/CLAUDE.md` (self-governing, needs its own edit) and
      consider proposing it for the shared `CORE.md` template (separate repo, would make it
      universal across every machine/project). Low priority — deferred until the TebelloReborn
      PNet/Careers24 work above is complete, per Tebello's explicit prioritization.

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
- [x] Pappa T vault survey — surveyed this machine for projects not yet tracked
      in the `Claude-Code/knowledge/INDEX.md` cache (mirrors the Operations vault
      survey pattern). Resolved the `Claude-Code/` "untracked nested repo" flag
      from an earlier `/continue` run (it's a deliberate, already-pushed sibling
      repo, not stray work). Filled TebelloReborn's previously-flagged knowledge
      gap and added 4 more sub-project knowledge files (`ai-outreach-agency`,
      `mims-app`, `iq-signal-generator`, `tenders-sa`). Noted `~/OneDrive/` and
      `~/Documents/Codex/` as data-only (no dedicated file); confirmed no other
      dev-root folders exist on this machine. See `session-log.md` for full detail.
