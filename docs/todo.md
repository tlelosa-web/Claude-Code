# Pappa T — Hub Task Queue

> This file previously held `ai-outreach-agency`'s task queue — a leftover
> from when this repo's root *was* that project, before the 2026-07-18 vault
> import restructured it under `ai-outreach-agency/`. That project's live
> queue is now self-governed at `ai-outreach-agency/docs/todo.md`. This file
> tracks hub-level tasks only: cross-project work and anything started at
> the vault root.

## In Progress

_(none active at hub level — see Backlog for the one remaining TebelloReborn follow-on item)_

## Next up

_(none active at hub level right now)_

## Closed — on hold pending affordability

- `ai-outreach-agency`: OpenRouter credits top-up (openrouter.ai/settings/credits) —
  `asset_gen` has been blocked on HTTP 402 since 2026-07-04. Closed, not an active task;
  revisit once affordability improves. Build Queue A (headless Claude Code migration) is
  the actual planned resolution and doesn't depend on this.

## Backlog

- [ ] `TebelloReborn` follow-on (lighter weight, not blocking): two Open Items remain in
      `TebelloReborn/docs/todo.md` from the PNet/Careers24 build — extraction reliability at
      scale (`qwen3:8b` on messier real-world job-posting text vs. dedicated-actor JSON) and
      confirming `CRAWLER_RATE_LIMIT_PER_MIN`'s default of 30 is conservative enough once real
      (non-fallback) PNet crawls are in regular use. Both are evidence-based revisits, not
      known bugs — pick up only if real usage surfaces a problem.
- [ ] Investigated 2026-08-01, re-verified 2026-08-01 against code + current Firecrawl docs: swap
      Apify's generic `website-content-crawler` actor for a self-hosted Firecrawl instance (AGPL-3.0,
      $0 marginal cost once running — fits the Ollama/headless-Claude-Code "local over paid API"
      pattern already used in both projects). Applies to exactly 2 of the 3 Apify call sites —
      `ai-outreach-agency/src/research/apify_client.py` and `TebelloReborn/src/vacancy_search/crawler_client.py`
      (both confirmed calling the identical generic actor URL and parsing the same dataset-items
      array shape). **Does not apply** to `TebelloReborn/src/vacancy_search/apify_client.py`'s dedicated
      Indeed/LinkedIn actors (confirmed — calls `misceres~indeed-scraper` / `bebity~linkedin-jobs-scraper`,
      not the generic crawler) — Firecrawl has no job-board-specific equivalent, so that would mean
      rebuilding Indeed/LinkedIn extraction from scratch (raw fetch + local Ollama extraction, same
      shape as the PNet/Careers24 build), not a client swap.
      Real work either way: self-host stack is actually **5 services** (API + Playwright + Redis +
      RabbitMQ + Postgres, not 4 as originally noted), and current self-host docs put RAM at
      **~8–12 GB minimum** — a real, ongoing resource cost on the same desktop that already runs
      `qwen3:8b` in Ollama for both projects' inference, competing for the same headroom. Both
      clients' response-shape parsing would also need rewriting (Firecrawl's `/v2/scrape` returns
      markdown/HTML/JSON directly, not Apify's dataset-items array).
      Self-hosted Firecrawl confirmed lacking their managed "Fire-engine" anti-bot/stealth layer —
      falls back to plain Playwright, weaker against Cloudflare-class protection — a real risk for
      bot-hostile job boards, less so for the two applicable call sites here (generic company-site and
      PNet/Careers24 crawling). AGPL-3.0's copyleft/publish-modifications clause only triggers if
      modified *and* offered as a network service to others — pure internal self-use on one desktop
      for these two projects doesn't trigger it, so licensing is a non-issue in practice, not a real
      constraint. Not urgent — neither project's active blocker is scraping-related right now, and the
      RAM finding makes it less attractive to pick up soon, not more. Backlog candidate only; write a
      spec/ADR if picked up.

## Completed

- [x] `Tenders`: archived the Eskom ITT E2142CXMWPR bid (`Enterprise Historian Licence,
      Maintenance & Support`) — Tebello confirmed 2026-08-01 it was abandoned. Folder renamed
      `110320262657` → `ARCHIVED_110320262657_Eskom_E2142CXMWPR` with an `ARCHIVED_STATUS.md`
      marker added (`80aed74`, `c63ac32`). Content preserved as-is (real ITT annexures, drafted
      bid returnables, costing, final packaged submission zip) — nothing deleted.
- [x] Promoted the "Codex-review + fold strongest points into spec before build" standard
      procedure to the shared `CORE.md` template as Universal Hard Rule #9 (v1.0 → v1.1,
      `375df47` in `tlelosa-claude-config`, pushed to `origin/main`) — now universal across
      every machine/project via the `dcoe-roster` plugin instead of copy-pasted per project.
      Wording matches the existing per-project copies verbatim.
- [x] Propagated the "Codex-review + fold strongest points into spec before build" standard
      procedure to `ai-outreach-agency/CLAUDE.md` Hard Rule #13, matching the exact wording
      already used in `TebelloReborn/CLAUDE.md` Hard Rule #13.
- [x] `ai-outreach-agency`: fixed local Ollama generation-latency false-positive risk —
      `research/ollama_client.py` `READ_TIMEOUT` bumped 60s → 120s and `"keep_alive": "30m"`
      added to the `/api/generate` payload (`3ec16cd`, docs update `1b80d0c`). 156 tests
      passing in that sub-project, zero regressions.
- [x] `TebelloReborn`: PNet/Careers24 Vacancy Coverage build, Automated Discovery redesign
      (spec: `TebelloReborn/docs/specs/pnet-careers24-coverage.md`, Phases 9–15, steps 55–80).
      Reviewer-approved "APPROVE WITH NITS" (no blockers); both nits fixed TDD and merged to
      `master` 2026-07-31 — W1 (extraction-prompt untrusted-text wrap, matching `doc_gen`'s
      `wrap_untrusted_text()` pattern) and W2 (`normalize_url()` allowlist-based tracking-param
      strip, preserving Indeed's `?jk=` identifier instead of collapsing all Indeed URLs to one
      dedupe key). Worktree `agent-a6eb29f112cbc6764` fast-forward merged (`9319b5a`), 232 tests
      passing, worktree removed. `data/discovery_config.json`'s `pnet.mode` flipped
      `"manual_pending_verification"` → `"auto"` (`bd72266`) per Tebello's browser-verified
      confirmation that PNet's bare-path search URL renders real results. See
      `TebelloReborn/docs/todo.md` and `TebelloReborn/docs/session-log.md`'s 2026-07-31 entry
      for full detail.
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
