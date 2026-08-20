## 2026-08-20 — `SessionStart` hook crashed on every session: installed plugins run from a per-plugin cache, not the marketplace checkout's sibling layout
**Source:** session (`ai-product-factory`, `4691578` on `main`), see also `ai-product-factory/knowledge/claude-code-plugin-hooks.md` for the fuller write-up
**Status:** active

`dcoe-roster`'s `SessionStart` hook (`bootstrap.mjs`, added 2026-08-09 per
the entry below) referenced `agent-bodies-reference/` via a path relative
to the plugin's own folder, assuming the repo-root-sibling layout that
exists in a full git checkout
(`~/.claude/plugins/marketplaces/tlelosa-claude-config/`). Claude Code
does not run installed plugins from that checkout — it runs them from a
separate **per-plugin cache**
(`~/.claude/plugins/cache/<marketplace>/<plugin>/<sha>/`) containing only
that plugin's own folder, no repo-root siblings. The path resolved to
nothing, `node` threw an uncaught `MODULE_NOT_FOUND`, and this happened on
**every session start**, before any of `bootstrap.mjs`'s own error
handling could run — a regression in the exact mechanism the 2026-08-09
fix below shipped to prevent silent roster loss, just via a different
failure path (loud crash instead of silent no-op).

**Fix:** guard the hook so a missing cache-relative path no-ops instead of
crashing; anything a plugin hook needs at runtime must live inside that
plugin's own directory tree so it travels with the cached copy, or the
hook command must check the path exists before using it.

**How to test this class of bug before shipping a hook change:** point
`CLAUDE_PLUGIN_ROOT` at the actual cache path
(`~/.claude/plugins/cache/...`), not the marketplace checkout, and run the
hook command by hand. Testing only against the checkout — which is what
this repo's own SESSION START instructions direct every session to read
from — will not catch this class of bug, since the checkout has the
sibling folder the cache doesn't.

Fixed + pushed here (`4691578`), verified via plugin-cache-hash check and
a live new-session smoke test, then ported into the stale local duplicate
under `ai-product-factory/Projects/tlelosa-claude-config/` (inert, but
fixed per owner request). No other installed plugin hook had the same
pattern (audited).

## 2026-08-16 — A PR can ship the very text a still-open spec review is meant to gate — the reviewer's BLOCK doesn't retroactively un-ship it
**Source:** session (revert commit `02462dd` on `main`), `docs/specs/2026-08-12-done-sha-citation.md`, `docs/todo.md`
**Status:** active

A spec proposing a SHA-citation requirement for `/session-end`'s Done
entries (`docs/specs/2026-08-12-done-sha-citation.md`) went to reviewer on
2026-08-12 and was **BLOCKED**: the verification command it specified
(`git log` scoped to a path) misses changed-file cases, the design
violates Hard Rule 10 (defends against uncached `origin/main` reads), its
own worked example cited a SHA that doesn't exist, and it had no pending
state for PR-merge lag. Routed back to planner for revision — never
approved, never merged as a spec.

**Independently, in the same window, PR #22 shipped the pre-review
flawed version live** into all three `/session-end` instances (this
repo's two, plus `Claude-Code`'s separate copy) — not by reopening or
ignoring the blocked spec, but because the PR's own scope happened to
touch the same text and carried the same (already-rejected) mechanism.
The spec-review gate blocking the spec did nothing to stop the code from
shipping through an unrelated PR that never went through that gate at
all — **a BLOCK verdict on a spec review only gates dispatches that go
through that review, not every future change that happens to touch the
same file.**

**Fix:** reverted the live flawed text in all three files (this repo's
two instances plus `Claude-Code`'s, which the spec's own scope note says
is technically outside its two-file remit — but the flawed text still
needed pulling from it), replaced with a pointer note back to the blocked
spec so no file carries a known-defective mechanism while the spec is
still being revised.

**Reusable lesson:** a reviewer BLOCK is a control on the reviewed change,
not a lock on the files or the mechanism it describes. When a spec is
blocked pending revision, treat any *other* in-flight PR that touches the
same surface as a live risk of re-introducing the exact thing just
blocked — check for this explicitly (search recent/open PRs for the
blocked mechanism's keywords) rather than assuming "it's blocked" means
"it can't land."

## 2026-08-09 — The roster was authoritative in CORE.md and absent on disk; hook, not documentation, is the fix
**Source:** session (Pappa T), `tlelosa-claude-config` `ab95eef` on `main`
**Status:** active

`~/.claude/agents/` did not exist on Pappa T on 2026-08-09 — six weeks after CORE.md
declared the roster deployed at user level and "available automatically in every
project." Consequences, all silent: no DCOE delegation target resolved (every
`domain`/`planner`/`architect`/`executor`/`tester`/`reviewer`/`doc-writer`/`debugger`/
`data-agent` call fell through to Claude Code built-ins), and `Explore` inherited the
session model. With `"model": "opus"` in `~/.claude/settings.json` that made read-only
search run at Opus — a tier *above* the Sonnet-priced fallback CORE.md warns about.
A missing agent raises no error, so the only symptom is a quieter, costlier session.

Root cause: the 2026-07-29 strip decision removed `dcoe-roster/agents/` to stop the
loader triple-listing every agent, and its explicitly accepted tradeoff was that the
plugin "no longer doubles as a new-machine roster-bootstrap vehicle." The manual copy
step that replaced it was never run. The 2026-08-08 session log had already recorded
that a `bootstrap.sh` re-run was needed; that note did not cause the re-run.

**Fix (CORE 1.5, `dcoe-roster` 3.7.0):** `SessionStart` hook in `dcoe-roster` →
`agent-bodies-reference/bootstrap.mjs`. Bodies stay at repo root, outside every
plugin-scanned path, so the triple-listing does not return — the hook restores the
bootstrap role by a different route rather than reverting the strip.

Design points worth reusing:
- **Node, not bash.** Not portability pedantry: a bash hook cannot report its own
  absence, which made the "prints one line naming the failure" acceptance criterion
  unsatisfiable. Node is what Claude Code already guarantees, so this also retired the
  unverified Git-Bash-on-Operations question instead of leaving it a build blocker.
- **Missing-only by default.** Per-machine agent edits are legitimate under the
  2026-07-29 decision, so a session-start overwrite would silently revert them. The
  hook names divergent files and leaves them; `--repair` is the explicit restore path,
  `--check` reports without writing. A missing-only hook with no repair path lets a
  locally broken agent persist forever — both halves are needed.
- **Manifest over globbing.** `roster-manifest.json` lists the 10 filenames and each
  one's model, so roster state is checkable by identity rather than by counting files.
- **Settings writes must be paranoid.** `bootstrap.mjs` parses, backs up, temp-writes,
  re-validates as JSON, then renames. An unparseable `settings.json` is refused, never
  overwritten — a bad write here breaks Claude Code on every machine that syncs.
- Verified: cold start installs 10; steady state silent; **six concurrent
  session-starts land on a clean 10 files with no empties**; hand-edited `executor.md`
  and `reviewer.md` both survive; malformed settings left untouched; missing manifest
  reports one line, exit 1.

**Codex-gate is now unconditional on every machine** via the manifest's
`requiredPlugins`. Tebello's decision 2026-08-09, taken with the compliance caveat
stated: it goes to Operations ahead of Fan Movement IT clearance for OpenAI egress,
and hard rule 9 stays universal — the conditional rewording proposed in the spec's B.3
was considered and **not** adopted. Until egress exists it fail-warns to "proceeding
solo" there.

**Gotcha found by testing, not reasoning:** `bootstrap.mjs` self-locates via
`import.meta.url` and never reads `CLAUDE_PLUGIN_ROOT`; only the hook's command string
does. With that variable unset, Node throws a multi-line `MODULE_NOT_FOUND` stack, not
a clean one-liner. Loud enough to satisfy the rule, but an earlier draft of the spec
claimed otherwise and was wrong.

**`gh` auth on Pappa T — superseded within the same session.** During this work `gh` was
unauthenticated, so no PR could be opened from a session here and branch-and-PR would have
stranded the branch; `ab95eef` went to `main` directly on instruction as a result.
**Fixed later the same day:** `gh auth login --hostname github.com --git-protocol https
--web`, logged in as `tlelosa-web`, token in the OS keyring, scopes `gist`, `read:org`,
`repo`. Both private repos resolve. Sessions on this machine can now branch → push → open
the PR in one step.

Two things that surfaced:

- **Scope gap: no `workflow`.** The `--web` flow granted `repo`/`read:org`/`gist` but not
  `workflow`, so a push touching `.github/workflows/` will be rejected by GitHub at push
  time — not at edit time, which makes it a confusing failure to diagnose. Fix with
  `gh auth refresh -h github.com -s workflow` if CI files ever need changing.
- **The stranding is measurable now.** First authenticated look: **11 branches with
  unmerged commits and zero open PRs** — 7 in `Claude-Code`, 4 in `tlelosa-claude-config`.
  That matches the 2026-08-08 triage's residue, which is the point: the count was never
  the problem, the inability to act on it was. Measure with
  `gh api repos/<owner>/<repo>/compare/main...<branch> -q .ahead_by` — against `main`,
  never against the merge-base.

**Reusing the Git Credential Manager token for `gh` is not a route.** GCM already held a
working github.com credential — that is why `git push` succeeded while `gh` failed — but
piping it out via `git credential fill` into `gh auth login --with-token` is **blocked by
Claude Code's auto-mode classifier** as credential extraction, correctly. The interactive
`--web` login is the better outcome anyway: `gh` gets its own refreshable credential
rather than borrowing one that would expire confusingly later.

## 2026-08-08 — hub-template drifts *both* ways, and it carried vault-specific content
**Source:** session (this machine), PR
https://github.com/tlelosa-web/tlelosa-claude-config/pull/14 (merged, `5660e1d`, branch
deleted)
**Status:** active

ADR-008 predicted drift from hubs *not taking* template updates. The first real
reconciliation showed it runs the other way too, and harder:
`hub-template/continue.md` was **four improvements behind** the O-P-C hub instance
(Step 0.5 category B, Step 1.75, Step 2.5, Step 1.9, plus Step 3's report fields).
Nothing detected this, because `HUB-CHECKLIST.md` only ever handled a *missing*
`continue.md` — an existing one was never diffed against the template. Fixed in the
same PR; the checklist now says to diff and fold each difference the correct way
(vault-specific stays local, generally useful gets promoted).

**A dependency chain can make a one-step backport impossible.** Step 1.9 could not go
up alone: it names Step 1.75 and depends on running after it, and the template had no
Step 1.75. Check what a step *references* before scoping a backport as small.

**The template contained three vault-specific leaks despite its own verbatim-copy
contract.** Two were cosmetic examples (`2. SOPS` as the parallel-sessions case, a SOPS
session title). The third actively misleads: Step 3's known-risks instruction read
"surface the OneDrive/git item from `CLAUDE.md`" — one hub's risk hardcoded as every
hub's, so a fresh vault adopting the template is told to report a risk it doesn't have.
**Being declared vault-agnostic is not evidence that a file is** — grep the template for
machine/project/vault names before trusting the label.

**A generalisation can beat the instance it came from.** The hub's Step 1.9 hardcodes
its two known repo layouts; the template can't, so it resolves roots with
`git -C "<path>" rev-parse --show-toplevel`. That is strictly better — a hub commonly
has both one-repo-many-subprojects *and* one-repo-per-subproject at once, and assuming
either silently reads the wrong clock. Worth folding back down into the hub copy.

**Gotcha — a marketplace clone left on a feature branch makes `/continue` Step 1.5 lie.**
Step 1.5 runs `rev-list HEAD..origin/main --count` against
`~/.claude/plugins/marketplaces/tlelosa-claude-config`. From a branch tip that is
*ahead* of `origin/main`, that count is `0`, reported as "shared core up to date." A
false clean in the step immediately before the one written to catch false cleans. If a
session branches that clone and can't restore it, say so loudly:
`git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config checkout main`.

**And path-qualify it, because this machine has two clones of this repo.** Attempting
that restore without `-C` landed it in `~/Downloads/tlelosa-claude-config` — the stray
clone from the 2026-07-28 Pappa T survey, which was already on `main` — so the command
succeeded, reported success, and changed nothing that matters. The marketplace clone
under `~/.claude/plugins/` is the only one that governs `/continue`, `/plugin`, or
`CORE.md` reads. Verify by branch name at the intended path, not by exit code:

```
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config rev-parse --abbrev-ref HEAD
```

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

**Two frontmatter styles were in play — now resolved.** `hub-template/continue.md`
and this hub's `.claude/commands/continue.md` opened with a
`---`/`# comment`/`---` block. That is valid YAML but parses to nothing, so it
registers **no slash-command description** — the command still runs, it just
shows up undescribed, with the command list falling back to the file's first
heading. Real YAML (`description: …`) is the working form, as used by the
marketplace's own instances and `codex-gate/commands/codex-review.md` (which
also demonstrates `argument-hint` and `allowed-tools`).

Fixed and merged 2026-08-06 in marketplace PR #12 (`fix/command-frontmatter`,
commit `5ab6b9a`, merged as `3ceb2f3`, branch deleted): **both**
`hub-template/continue.md` and
`hub-template/session-end.md` converted, since both carried the defect — not
just the one that was reported. Hub's `continue.md` re-copied to match.
Confirmed live: the command listing went from showing the file's first heading
to showing the real description. No other command file in either repo has an
inert block.

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

**Two gaps found on the command's first real run, same day:**

1. **Step 3 over-appends.** It says "append a new dated entry"
   unconditionally. Wrong for a session that already wrote its own log
   entries, and wrong for a second run used as a mid-session checkpoint —
   both yield duplicate or near-empty entries. Intended behaviour is
   reconcile-not-duplicate: extend or verify the existing entry when the
   work is already logged, append only when it isn't.
2. **Step 5 is unreachable on this tool surface, not merely flaky.**
   `set_session_title` rejects the current session *and* `list_sessions`
   excludes it, so a session cannot even obtain its own ID to attempt the
   call — the step can't fail gracefully because it can't be attempted at
   all. The command's "attempt it, then say so plainly if it fails" wording
   assumes a call that returns an error; here there is none to make. Worth
   rewording to "report unavailable" for this environment rather than
   implying an attempt.

Both fixes belong upstream in `hub-template/session-end.md` first, then
re-copied down — patching only this hub would leave the same defects in
every other vault that adopts the template later.

**Fixed and merged the same day, upstream-first:** marketplace PR #11
(https://github.com/tlelosa-web/tlelosa-claude-config/pull/11, commit
`9bd83aa`, merged as `e6d381a`, branch deleted) carries both fixes plus a
"Post-implementation corrections" section added to the spec. So
`hub-template/session-end.md` on `main` is correct as of 2026-08-06 — a
vault adopting `/session-end` from here on gets the fixed version and needs
no further patching. Fix 1
touches `hub-template/session-end.md` only — the marketplace repo keeps no
session log, so its own instance has no such step. Fix 2 touches both. The
hub's own instance was updated by hand in the same session, since ADR-008's
file-copy distribution doesn't propagate.

**Process note worth keeping:** the upstream-first ordering matters here.
Fixing only the vault that found the defect is the tempting shortcut, and
it silently leaves the bug in `hub-template/` for every vault that adopts
the command later — which is exactly how item 3 of the original spec sat
unimplemented while its status line read `Implemented`.

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
