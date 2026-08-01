# Session Log

## 2026-08-01 (cont'd)

- Reviewed the Firecrawl-swap backlog investigation: verified its code claims directly against
  `ai-outreach-agency/src/research/apify_client.py`, `TebelloReborn/src/vacancy_search/crawler_client.py`,
  and `TebelloReborn/src/vacancy_search/apify_client.py` (all confirmed accurate — 2 generic-actor call
  sites, 1 dedicated-actor call site correctly excluded), and cross-checked its Firecrawl claims against
  current self-host docs via web search. Found two corrections: the self-host stack is 5 services
  (missing RabbitMQ from the original note) and needs ~8–12 GB RAM minimum, not just "a Docker Compose
  stack" — a real resource cost competing with Ollama on the same desktop. Also softened the AGPL risk
  note — the copyleft/publish clause only triggers on modify-and-offer-as-a-service, which doesn't apply
  to internal self-use. Folded all corrections into the `docs/todo.md` backlog entry; kept it a backlog
  candidate (not started) per Tebello's decision — the RAM finding makes it less attractive to pick up
  soon, not more.

## 2026-08-01

- Promoted the "Codex-review + fold strongest points into spec before build" standard
  procedure from a 3-place copy-paste (hub `CLAUDE.md` Pattern 1, `TebelloReborn/CLAUDE.md`
  Hard Rule #13, `ai-outreach-agency/CLAUDE.md` Hard Rule #13) into the shared `CORE.md`
  template as Universal Hard Rule #9 — v1.0 → v1.1, committed and pushed (`375df47`) to
  `tlelosa-claude-config` on `origin/main`. Wording matches the existing per-project copies
  verbatim. Every machine picks it up on next `/plugin marketplace update
  tlelosa-claude-config`; no silent auto-apply. Closes the last open backlog item from this
  hub's `docs/todo.md`.

## 2026-07-28

- **Pappa T vault survey** (mirroring the Operations vault survey pattern): surveyed
  this machine's dev locations for any project not yet tracked in the shared
  `Claude-Code/knowledge/INDEX.md` cache. Checked home directory, Desktop, Documents,
  Downloads, and OneDrive — confirmed no `~/Dev`/`~/Projects`/similar dev-root exists
  on this machine; `Pappa T/` is the only project folder on Desktop.
- Found and resolved the `Claude-Code/` folder flagged as an "untracked nested repo,
  unclear origin" by an earlier `/continue` run this session: it's `knowledge/`, a
  separate, deliberate, already-committed-and-pushed git repo (remote
  `tlelosa-web/Claude-Code`) that serves as a cross-machine knowledge cache shared
  between Pappa T and Operations. It sits physically inside the Pappa T vault folder
  but is intentionally its own repo, not a submodule — nothing to clean up.
- Read that cache's `knowledge/INDEX.md` and found none of Pappa T's five sub-projects
  (TebelloReborn, ai-outreach-agency, MIMS App, IQ, Tenders) had a dedicated entry —
  only the vault itself (`pappa-t.md`) did, which had already flagged TebelloReborn as
  a known gap to fill. Wrote all five as new knowledge files, respecting the cache's
  no-company-data rule (public-repo-level detail only):
  - `tebelloreborn.md` — Career Engine pipeline, ADR-003 inference split, the
    doc-gen prompt-injection fix (untrusted job-posting text → headless Claude Code),
    fpdf2 `multi_cell` gotcha, Apify payload-shape bug.
  - `ai-outreach-agency.md` — pipeline shape, ADR-004, the two still-open items below,
    two wiring bugs caught only by integration tests (not unit tests).
  - `mims-app.md` — Next.js/Supabase MRP app; noted it's driven by `GEMINI.md` rather
    than `CLAUDE.md`, unlike every other sub-project here; Shop Floor stage in progress.
  - `iq-signal-generator.md` — regime-filtered trading-signal CLI, ADX/RSI/Stochastic
    logic and hardcoded risk-management stops.
  - `tenders-sa.md` — SA tender-monitoring automation; confirmed the `tenders-sa`
    submodule resolution from the 2026-07-18 session is intact; noted a dormant
    tender-bid-package folder structurally only (no bid content).
- Updated `pappa-t.md` with a dated entry recording this survey's findings, and
  `knowledge/INDEX.md` with rows for all five new files.
- Noted `~/OneDrive/` (personal CVs/spreadsheets/scans) and `~/Documents/Codex/`
  (empty) as data-only, no dedicated file needed; `~/python-sdk/` is a downloaded
  Python runtime, not a project. `~/Downloads/tlelosa-claude-config/` (+ a `.zip`)
  is a redundant extra clone of the already-tracked marketplace repo — skipped per
  the remote-match dedupe rule.
- Surfaced two open items from `ai-outreach-agency`'s own `docs/todo.md` up to this
  hub's `docs/todo.md` "Next up" (same pattern as the Operations survey adding
  SOPS's two items): topping up OpenRouter credits (blocks `asset_gen` batch runs,
  HTTP 402 since 2026-07-04) and a small Ollama read-timeout/keep-alive fix
  (mitigates intermittent false-positive timeouts on real batches).
- Committed and pushed the `Claude-Code` knowledge-cache changes; committed the
  `docs/todo.md`/`docs/session-log.md` changes in this repo (no remote configured
  here, so no push).

## 2026-07-18

- Imported the Master Vault structure into this repo — strategic docs, CVs,
  and sibling projects (`8612c8e`). This repo had been `ai-outreach-agency`'s
  own root until this point; the import restructured it under
  `ai-outreach-agency/` and brought in `MIMS App/`, `IQ/`, `TebelloReborn/`,
  `Tenders/`, and the vault-level strategy/finance/brand folders.
- Aligned the project with the `dcoe-roster` v3.2 template — rewrote
  `CLAUDE.md`, added `.claude/settings.json` deny-list for destructive
  commands, removed stale project-level agent overrides in favor of the
  user-level `~/.claude/agents/` roster (`48e13d5`).
- Renamed the vault to Pappa T, documented `ai-outreach-agency` as a
  self-governing sibling project, and flagged known structural drift —
  `TebelloReborn/.claude/agents/` carrying a full roster fork instead of an
  override, and `Tenders/4_Scripts/tenders-sa/` as an untracked nested repo
  (`39ee392`).
- Wrote `docs/folder-structure.md`, an as-is snapshot of the vault's actual
  directory layout distinct from the aspirational structure in `CLAUDE.md`
  (`c7791c7`).
- Wired up the hub-and-spoke pattern: added the CORE.md read-instruction to
  `CLAUDE.md` and copied the `/continue` command (previously only present
  in `ai-outreach-agency/.claude/commands/`) into the vault root's
  `.claude/commands/` (`5620fd1`).
- Ran `/continue` from a fresh session to verify the wiring above actually
  works — confirmed it resumes correctly from this vault's own
  `docs/todo.md`/`docs/session-log.md`, not silence or another project's
  data.
- Renamed 3 stale `"Continuation"`-titled sessions to reflect their actual
  work, and archived 3 sessions whose work was already fully committed or
  superseded by later commits.
- Found and fixed `docs/todo.md` and this file itself: both were leftover
  artifacts from when this repo was `ai-outreach-agency`'s root —
  `docs/todo.md` still held that project's task queue (superseded by its
  own copy at `ai-outreach-agency/docs/todo.md`), and this log hadn't been
  updated since 2026-06-01.
- Ran `/continue` again: renamed the still-`"Continuation"`-titled session
  to reflect its actual work, and archived two more sessions whose tasks
  were fully committed — `Pappa T project brain review` (hub-and-spoke wiring,
  `5620fd1`, verified by this run) and `Rename home PC to Pappa T`
  (`tlelosa-claude-config`, `9e40d8a`, follow-up branch cleanup already done
  elsewhere).
- Fast-forwarded the local `tlelosa-claude-config` marketplace clone
  (`~/.claude/plugins/marketplaces/tlelosa-claude-config`) past the 2 pending
  upstream commits (`eff87e8` — home PC → Pappa T rename).
- Trimmed `CLAUDE.md` from 519 to 457 lines: removed the DCOE diagram,
  DCOE Rules list, sub-agent roster table, and model-routing table now that
  `CORE.md` (read every session) carries all of them verbatim. Also caught
  and corrected a doc-vs-reality drift — both `CORE.md` and this file
  described the default agent roster as living at `~/.claude/agents/`, which
  doesn't exist on this machine; the files actually deploy via the plugin to
  `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/agents/`
  (`d7bf782`).
- Re-investigated the flagged `TebelloReborn/.claude/agents/` "roster fork":
  diffed all 9 files against the shared defaults and found each one
  substantively rewritten around the Career Engine's own pipeline stages and
  hard rules, not a stale copy. TebelloReborn's own `CLAUDE.md` explicitly
  names that folder canonical, and the hub's own hub-and-spoke rule gives a
  sub-project's brain file precedence in its own folder. Replaced the
  "known violation" note in `CLAUDE.md` with one documenting this as a
  sanctioned override — no files deleted (`d7bf782`).
- Resolved the untracked `Tenders/4_Scripts/tenders-sa/` nested repo:
  registered it as a git submodule against its real upstream
  (`alfa-rsa/tenders-sa`) rather than vendoring or dropping it (`d6da4c3`).
  This closes out every item that was in `docs/todo.md`'s backlog.

## 2026-06-01

- Ran the Project Portfolio DCOE context pass over MIMS App, IQ, Tenders, and TebelloReborn.
- Created `docs/project-portfolio.md`; classified MIMS as the primary 30-day focus, TebelloReborn Career Engine as weekly support, Tenders as a narrow validation lane, and IQ as bounded risk/learning.
- Ran the first `identity-strengths` DCOE context pass using the master CV, LinkedIn guide, professional brand docs, project index, strategic framework, operational automation notes, and MIMS directive.
- Created `docs/strengths-profile.md`, identifying the core pattern as Strategic Operations Builder: shop-floor credibility plus systems, controls, communication, and practical automation.
- Reframed the workspace as TebelloReborn: a DCOE-governed personal operating system for life improvement, strengths discovery, project organization, and business/career leverage.
- Rebuilt `AGENTS.md` as the clean project brain.
- Added `docs/life-domains.md`, `docs/strengths-inventory.md`, and `docs/orchestration-model.md`.
- Added domain-specific executor agents for identity, career, operations, ventures, finance, governance, learning, wellbeing, and tenders.
- Read the Claude project brain and found it duplicated the DCOE instructions with broken encoding.
- Kept `AGENTS.md` as canonical.
- Renamed `Tebello Project` to `TebelloReborn`.
- Moved the top-level `CV` archive into `TebelloReborn/2_Source_Data/Legacy_CV_Archive/`.
- Created the DCOE docs and `.Codex/agents/` scaffold.
