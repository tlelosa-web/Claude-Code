## 2026-07-28 — Rollout PR merged; codex-gate + IT question still open
**Source:** session (cross-project status survey)
**Status:** active

PR #9 ("Mark marketplace validation and plugin rollouts complete") merged
into `main` — marketplace validation, dcoe-roster 3.3.0, document-skills,
and Context7 are all confirmed installed on both Operations and Pappa T.
The hourly watch-loop that had been polling this PR since 2026-07-26 was
stopped (trigger deleted) once it merged clean with nothing further to act
on.

Still open, per `docs/todo.md`'s "Open" section (not touched by PR #9):
- codex-gate install + network-off smoke-test on Pappa T
- copying the drafted codex-gate ADR into the Operations hub's
  `docs/decisions/`
- Fan Movement IT confirmation on whether OpenAI egress from Operations is
  covered (codex-gate stays Pappa T-only until then)

`dcoe-roster/CORE.md` is at **Core version 1.0** as of this check — DCOE
architecture (Domain → Context → Orchestrate → Execute), 9-agent roster,
Sonnet-5-medium default with evidence-based Opus escalation, reviewer
permanently on Opus.

## 2026-07-23 — Repo purpose & structure
**Source:** tlelosa-claude-config README.md, CLAUDE.md
**Status:** active

Private Claude Code plugin marketplace (Markdown + JSON only, no runtime/
tests/dev server). Cloned on two machines: **Operations** (work PC) and
**Pappa T** (personal). Hard rule: never contains company or project data.

Structure:
- `.claude-plugin/marketplace.json` — the catalog Claude Code reads.
- `dcoe-roster/` — DCOE sub-agent roster plugin (domain, planner,
  architect, executor, tester, reviewer, doc-writer, debugger,
  data-agent) + `CORE.md`, the shared architecture/rules doc every
  opted-in project reads at session start (not via `@import` — that
  doesn't resolve absolute paths outside the project tree, confirmed
  2026-07-18, see ADR-007).
- `shared-skills/` — cross-project Skills plugin (dev-server staleness
  check, safe office-file read, UI-primitive reuse, `/capture`, etc).
- `hub-template/` — vault-agnostic `/continue` skeleton + checklists
  (ADR-008) for running the hub-and-spoke pattern at any vault root.
- `codex-gate/` — advisory plugin, `/codex-review` sends one spec file to
  the OpenAI Codex CLI for a second opinion. Warn-only, never blocks.
- `docs/todo.md` / `docs/specs/` — task list and specs.

## 2026-07-23 — IT clearance status (Operations machine)
**Source:** tlelosa-claude-config README.md
**Status:** active

Cleared by Fan Movement IT (2026-07-21): personal Anthropic account
approved for use on the work PC, broad enough to cover Context7's
external MCP service. Repo still carries no company data regardless of
clearance — that's a hard rule, not contingent on IT policy.

**Not covered:** `codex-gate` (OpenAI egress). Needs its own confirmation
before installing on Operations — Pappa T only until then.

## 2026-07-23 — Open items (as of last check)
**Source:** tlelosa-claude-config docs/todo.md
**Status:** active

- codex-gate install + smoke-test still pending on Pappa T (network-off
  fail-warn path needs a real check).
- codex-gate ADR drafted (`docs/specs/2026-07-21-codex-gate-adr-draft.md`)
  but not yet copied into the Operations hub's `docs/decisions/`.
- Open question with Fan Movement IT: does OpenAI egress from Operations
  get covered? Blocks installing codex-gate there.
- Marketplace validation, document-skills install, dcoe-roster 3.3.0
  rollout, and Context7 install all still need to be run on both
  machines — consolidated steps in
  `docs/rollout-checklist-2026-07-21.md`.
