## 2026-08-06 — /session-end promoted to hub-template; hub instance adopted
**Source:** session (this machine, `TshepangLelosa`) + marketplace commits
`a56ea84`/`9a18c8f`, spec `docs/specs/2026-08-04-session-end-command.md`
**Status:** active

The marketplace added a `/session-end` command via the same ADR-008
file-copy promotion path `/continue` took: a vault-agnostic skeleton in
`hub-template/session-end.md`, plus per-vault instances copied from it.
It closes out a session — reconcile `docs/todo.md`, append the
`docs/session-log.md` entry, update `knowledge/`, set the session title —
so the next `/continue` run reads deliberate state instead of
reverse-engineering it from `list_events`.

**Gotcha — the spec says `Status: Implemented` but only 2 of its 3 files
existed.** Items 1 (`hub-template/session-end.md`) and 2 (the marketplace's
own `.claude/commands/session-end.md`) shipped in `a56ea84`; item 3,
`Claude-Code/.claude/commands/session-end.md` (the full hub instance), was
never created — this hub had only `continue.md` until 2026-08-06. Worth
remembering when reading that repo's spec statuses: "Implemented" there
tracks the marketplace side, and cross-repo items in the same spec can
still be outstanding. Check the target repo directly rather than trusting
the status line.

**Two frontmatter styles are in play.** `hub-template/continue.md` and this
hub's `.claude/commands/continue.md` open with a `---`/`# comment`/`---`
block, which is inert — it registers no slash-command description. The
marketplace's own newer `session-end.md` uses real YAML
(`description: …`). The hub's new `session-end.md` follows the YAML form;
`continue.md` was left as-is (working, just undescribed) rather than
changed as a drive-by.

**What the hub instance adds** over the shared skeleton, none of which is
in `hub-template`: a Step 0 Hard Rule 6 pull-first gate (this command
writes all three contention files, so it is the highest-risk command in the
hub for stale-base edits); an explicit post-append ordering check on
`session-log.md`; the `knowledge/` + `INDEX.md` step (Hard Rule 5); and the
📍 live-Desktop-copy caveat — check the live sub-repo's git state too, since
work pushed to `Desktop/Operations`/`Desktop/Pappa T` remotes doesn't reach
O-P-C until it's re-merged.

Distribution stays manual file-copy: improving one vault's `session-end.md`
does not propagate: backporting into `hub-template/` and re-copying is a
deliberate step, the same tradeoff ADR-008 already accepted.

## 2026-08-03 — codex-gate install + network-off smoke-test: both paths confirmed
**Source:** session (this machine, `TshepangLelosa`, post-Operations/Pappa T
consolidation — `codex-gate` is installed at the user level
(`~/.claude/plugins`), so it applies machine-wide, not per-project)
**Status:** active

Ran the smoke-test per `docs/specs/2026-07-29-codex-gate-pappa-t-smoketest.md`:

- **Confirmed installed:** `codex-gate` present in both
  `~/.claude/plugins/marketplaces/tlelosa-claude-config/codex-gate` and the
  plugin cache; `~/.claude.json` shows `codex-gate:codex-review` already
  used 3 times previously (last 2026-07-29), confirming it was reachable
  before this session too. Marketplace was already current (0 commits
  behind `origin/main` per the Step 1.5 check).
- **Network-available path:** ran `/codex-review` against a real spec
  (`docs/specs/2026-07-29-nameplatetool-test-suite.md`). Reached
  `chatgpt.com`'s Codex backend cleanly, returned a full structured second
  opinion in well under the 90s cap, appended to that spec file as its own
  advisory-note section. Confirms the happy path works end to end.
- **Network-off path:** forced an unreachable state by pointing
  `HTTP_PROXY`/`HTTPS_PROXY` at a closed local port (`127.0.0.1:1`) for
  just the one command invocation — a safe, reversible way to simulate
  network-off without touching the machine's actual adapter. Ran the same
  underlying `codex exec` call directly (not through the full skill, so it
  wouldn't append a second real advisory section to the same spec).
  **Real finding:** `codex exec` does not fail fast when it can't reach
  Codex — it logs loud `ERROR` lines (WebSocket connection refused, os
  error 10061) and retries its own reconnect logic ("Reconnecting...
  1/5" through "5/5", then falls back from WebSockets to HTTPS and retries
  again), and was still retrying when the skill's external `timeout 90`
  cap killed it (exit code 124). This confirms the skill's 90s cap is
  **load-bearing, not a formality** — without it, an unreachable Codex
  would hang well past 90s on its own internal retry loop. The skill's
  step 4 correctly treats any of "non-zero exit, empty output, or timeout"
  as fail-warn, so this path is legitimately caught by the existing
  design; nothing needs to change in the skill itself.

Both paths behave as designed. This closes the "codex-gate install +
network-off smoke-test" sub-item — the only remaining open codex-gate
sub-item is the Fan Movement IT confirmation on Operations egress (external,
not something a session can execute).

## 2026-07-29 — codex-gate ADR copied into this hub's docs/decisions/
**Source:** session (Operations ADR copy, via git — no local Operations
machine access needed since it was a straight file write through this
repo's own remote)
**Status:** active

Copied `tlelosa-claude-config/docs/specs/2026-07-21-codex-gate-adr-draft.md`
(content below its divider) into this hub's own `docs/decisions/` as
`ADR-009-codex-second-opinion-gate.md`, per the draft's own numbering
assumption (009). Content unchanged from the draft — no cross-reference
needed updating since the draft already pointed at the correct final
location.

**Gap discovered while doing this, now closed:** `docs/decisions/` didn't
exist in this hub repo before this task — despite `tlelosa-claude-config`'s
own README, `CORE.md`, and `HUB-CHECKLIST.md` all referencing "ADR-007" and
"ADR-008 in the Operations hub's `docs/decisions/`" as if they were already
recorded there. Wrote both up from what's actually documented across
`tlelosa-claude-config` (CORE.md's top-of-file distribution note, the
README's `dcoe-roster`/`hub-template` sections, `HUB-CHECKLIST.md`):
- `docs/decisions/ADR-007-core-md-read-not-import.md` — why `CORE.md` is
  distributed via a plain read instruction in each project's `CLAUDE.md`,
  not a Claude Code `@import` (confirmed 2026-07-18: `@import` doesn't
  resolve absolute paths outside the project tree).
- `docs/decisions/ADR-008-hub-template-promotion.md` — why the
  hub-and-spoke `/continue` pattern was extracted into
  `tlelosa-claude-config/hub-template/` as a vault-agnostic skeleton +
  reconciliation checklist, once it proved out on Operations. Date is
  approximate (dated to the `hub-template/` addition, not independently
  re-verified against commit history this session).

codex-gate itself stays **Pappa T-only regardless** — this copy only closes
the documentation sub-item, not the install. Still open, per
`docs/todo.md`:
- codex-gate install + network-off smoke-test on Pappa T
- Fan Movement IT confirmation on whether OpenAI egress from Operations is
  covered (codex-gate stays Pappa T-only until then)

## 2026-07-28 — Rollout PR merged; codex-gate + IT question still open
**Source:** session (cross-project status survey)
**Status:** superseded

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
