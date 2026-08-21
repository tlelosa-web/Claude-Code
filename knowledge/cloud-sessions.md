Findings about the Claude Code **remote/cloud execution environment** (web,
mobile, GitHub-triggered sessions) — the ephemeral container, its network
policy, and tooling quirks. Machine-specific findings for Operations and
Pappa T live in their own files (`operations-hub.md`, `pappa-t.md` — both
retired 2026-08-20, kept as history).

## 2026-08-06 — The agent proxy blocks arbitrary hosts; HTTP 000 ≠ empty page
**Source:** session (verifying a GitHub Pages deploy for RMLRACE/cratetracker)
**Status:** active

Outbound HTTPS goes through the agent proxy, which refuses hosts outside
the environment's network policy — **including a project's own GitHub
Pages site**. `curl https://<user>.github.io/<repo>/` returns **HTTP 000
with an empty body**, which reads exactly like "the page is blank or
stale" rather than "the request never left the container". Don't conclude
anything about content from it.

Diagnose with:

    curl -sS "$HTTPS_PROXY/__agentproxy/status"

It reports `recentRelayFailures`, e.g.
`{"kind":"connect_rejected","detail":"gateway answered 403 to CONNECT","host":"rmlrace.github.io:443"}`
— that's a policy denial, not a broken site. Never work around it by
disabling TLS verification or unsetting `HTTPS_PROXY`.

To verify a deploy actually shipped, go through the GitHub API instead:
find the workflow run whose `head_sha` matches the merge commit and assert
`status:completed` + `conclusion:success`, and read the deployed source
with `git show origin/main:<path>`. That proves the pipeline and the
source — but **not** the bytes the live URL serves, so say that plainly
rather than implying the site was checked.

## 2026-08-06 — `mcp__github__actions_list` blows the token limit
**Source:** session
**Status:** active

`list_workflow_runs` embeds a full `repository` object in *every* run, so
even `per_page: 2` returns ~200 KB, gets rejected, and spills to a
tool-results file you then have to parse anyway. Go straight to the REST
API and project only what's needed:

    curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
      "https://api.github.com/repos/OWNER/REPO/actions/runs?branch=main&per_page=3" \
      | python3 -c "import sys,json; [print(r['run_number'], r['head_sha'][:7], r['status'], r['conclusion']) for r in json.load(sys.stdin)['workflow_runs']]"

To *wait* for a run, wrap that in an `until` loop and start it with Bash
`run_in_background: true`. A foreground `sleep` is blocked outright, and
so is chaining shorter sleeps to get around it.

## 2026-08-06 — Playwright: global install, ESM resolution, and service workers
**Source:** session
**Status:** active

Chromium is pre-installed at `/opt/pw-browsers/chromium` — never run
`playwright install`. The `playwright` package is installed **globally**
(`/opt/node22/lib/node_modules`) and **`NODE_PATH` does not apply to ESM
`import`**, so `import { chromium } from 'playwright'` fails from a
scratch dir even with `NODE_PATH` set. Symlink it in instead:

    mkdir -p node_modules && ln -s /opt/node22/lib/node_modules/playwright node_modules/playwright

Then launch with `executablePath: '/opt/pw-browsers/chromium'`.

For **service-worker** work use `launchPersistentContext` (SWs need a
persistent profile; `rm -rf` the profile dir between runs for a clean
first-install test). `localhost` counts as a secure context, so
`python3 -m http.server` over a copy of the repo is enough. A real deploy
is simulated by **mutating the served files on disk mid-session** and
reloading — the browser byte-diffs `service-worker.js` and runs the
genuine update path, which is the only way to test install → waiting →
prompt → activate → reload end to end.

## 2026-08-12 — `git push origin --delete` returns HTTP 403 from cloud containers
**Source:** session (task: delete triaged branches; 2026-08-09 attempt)
**Status:** active

`git push origin --delete <branch>` fails with HTTP 403 from a Claude Code
cloud/web container, while ordinary pushes to the same remote succeed and
the agent proxy logs no failure. The session's git credentials (deployed as a
checkout credential helper) create and update refs but cannot delete them.

Workaround: delete branches from a surface with full git access — the
GitHub web UI. (Originally also named the Operations or Pappa T machine;
**corrected 2026-08-20** — both are retired, so the GitHub web UI is now the
only such surface, unless a future live machine replaces them.) Automation
that runs entirely in the cloud and needs to clean up branches after itself
is blocked at present.

**Scope:** This was measured on a restricted-access cloud container and does
not reproduce on the full-filesystem-access session surface (CCR with local
disk). A confirmed failure on one surface does not imply it everywhere.

## 2026-08-12 — A cloud container starts with stale `origin/*` refs, and a bad ref name aborts the whole fetch
**Source:** session (architecture export; both repos checked out together)
**Status:** active

A freshly-provisioned cloud session's checkout is **not** necessarily at
`origin/main`, and its cached remote-tracking refs can be well behind the real
remote. Measured this session: `Claude-Code` `HEAD` and its cached
`origin/main` both read `855f392`, while the actual `refs/heads/main` on GitHub
was `64583a0` — **13 commits ahead**. `tlelosa-claude-config` was behind by a
comparable margin. Nothing looks wrong: `git status` is clean, and
`git log origin/main..HEAD` returns empty, which reads as "up to date" when it
actually means "up to date with a stale cached ref."

Two compounding traps:

1. **The designated branch may exist locally and not on the remote.** Both
   repos had `remotes/origin/claude/system-architecture-download-injjbi` in
   `git branch -a`, and `git ls-remote --heads origin` showed no such ref on
   either remote. The tracking ref is created by the container's own setup, so
   `git branch -a` is not evidence a branch was ever pushed.
2. **`git fetch origin main <nonexistent-branch>` aborts entirely** with
   `fatal: couldn't find remote ref <branch>` — and because the fetch is
   atomic, `origin/main` is **not** updated either. Any `git log` comparison
   run after that fatal silently answers from the stale ref. This is the
   `..`-range-operator shape from `session-tooling.md` again: the command
   returns a plausible wrong answer instead of failing visibly.

**Practice:** at the start of a cloud session, verify against the remote itself
rather than the cached ref, and fetch one ref at a time so a bad name cannot
take the good fetch down with it:

    git ls-remote --heads origin              # ground truth, no local cache
    git fetch origin main                     # separately from any branch fetch
    git rev-list --count HEAD..origin/main    # 0 only after a *successful* fetch

Where the working branch holds no unique commits,
`git merge-base --is-ancestor HEAD origin/main` confirms a `reset --hard
origin/main` discards nothing — check it rather than assuming.

**Consequence worth noting:** anything read before that fetch is suspect. This
session first reported a `roster-manifest.json` `coreVersion` drift (manifest
`1.4` vs `CORE.md` `1.5`) that was real in the stale checkout and **already
fixed on main**, where both read `1.6`. A stale checkout does not just hide new
work — it manufactures findings that are no longer true.

## 2026-08-20 — No registered `reviewer` sub-agent type in this environment; simulate it via a general-purpose Agent call
**Source:** session (reviewer pass on two `tlelosa-claude-config` specs, `docs/specs/2026-08-20-verify-fetch-succeeded-hard-rule-10.md` and `docs/specs/2026-08-20-cross-project-knowledge-checklist.md`)
**Status:** active

`ls ~/.claude/agents/` is empty in this cloud environment — the `dcoe-roster`
plugin's `SessionStart` hook (which populates it, missing-only, from
`agent-bodies-reference/`) apparently doesn't run here, or hasn't yet at the
point a session needs it. The `Agent` tool's available `subagent_type`
values are the generic built-ins (`general-purpose`, `Explore`, `Plan`,
`claude-code-guide`, `statusline-setup`) — no `reviewer`, `architect`,
`executor`, etc. registered as first-class agent types, even though
`tlelosa-claude-config/agent-bodies-reference/reviewer.md` (and the other 9
roster bodies) exist as files in a checked-out repo.

**Workaround that worked:** dispatch a `general-purpose` Agent call with
`model: "opus"` (matching `reviewer.md`'s own `model: claude-opus-5`
frontmatter) and a prompt that embeds the persona verbatim — its review
criteria, its read-only/report-don't-fix constraint, its
APPROVE/APPROVE WITH NITS/BLOCK output format — rather than relying on a
`subagent_type` that doesn't exist here. Worked across three review passes
on the same spec (two BLOCKs, one APPROVE WITH NITS), each independently
verifying every factual claim in the spec against the real files rather than
trusting the spec's own prose — exactly the read-only, verify-don't-trust
behavior the real persona file asks for.

**Why this matters:** any DCOE hard rule that names a specific roster agent
by role (reviewer gates every spec per Hard Rule 9/repo-specific rules,
`architect` for schema decisions, etc.) is satisfiable from a cloud session
even when the roster isn't installed as first-class agent types — the
persona file is the actual contract, and the `Agent` tool's model override
plus a persona-embedding prompt reproduces it faithfully. Don't skip a
reviewer gate here just because `subagent_type: "reviewer"` isn't listed;
read the persona file and simulate it instead.

## 2026-08-20 — A proper-noun grep survey cannot prove completeness; the real recurring miss was document position, not vocabulary
**Source:** session (Operations/Pappa T historical-reference sweep,
`tlelosa-claude-config/docs/specs/2026-08-20-operations-pappa-t-historical-sweep.md`)
**Status:** active

A docs-only cross-repo sweep (retiring stale "Operations/Pappa T are live"
language across three repos) went through five real BLOCK→fix review rounds
with a simulated `reviewer` (the workaround above) before a sixth was cut
short by hitting this account's monthly spend limit. Two findings worth
keeping past that specific task:

**A `grep -i 'Operations|Pappa T'` survey cannot prove a repo is clear.**
Present-tense claims describing the same retired fact were repeatedly
phrased without either proper noun — "both machines," "each machine," "an
employer machine" — and survived three consecutive review passes precisely
because the survey method was a proper-noun pattern search. Widening the
pattern (`both machines|each machine|employer machine|...`) closed most of
the gap but not all of it: one instance was split across a hard-wrapped line
("run on both\nmachines"), invisible to any single-line grep regardless of
pattern width. **A pattern search only tells you where the pattern matched
— it cannot tell you the file is otherwise clear, and stating "no further
hits" as a completeness claim is a bare assertion the tool itself cannot
support.**

**The actual recurring failure shape across all five review rounds was
document *position*, not vocabulary.** Concretely: a bullet-and-file
inventory (list every affected file, list every affected todo item) reliably
found live-machine assertions stated as their own bullet or their own dated
entry, but reliably *missed* the same claim restated in a **section
preamble** (text that introduces several bullets below it), an **INDEX.md
summary row** (a one-line restatement of a file's content, for a reader who
doesn't open the file), or a **table cell**. Three separate section
preambles and three separate INDEX rows were each caught only on a later
pass, after the bullets/files they governed had already been fixed —
producing a section that would have contradicted itself the moment the fix
landed (the bullets corrected, the preamble introducing them still asserting
the old state). The generalizable rule: **a claim restated *about* content
elsewhere (a preamble, a summary row, a table cell) is exactly as much a
live assertion as the content itself, and a survey scoped to "files and
bullets" will not enumerate it** — check preambles and summary/index rows
as their own category, not as incidentally covered by the file or bullet
they describe.

**On stopping a review loop:** five rounds of real, independently-verified
findings with genuinely shrinking severity (major scope gaps → a single
misattributed quote and a stale index-row phrase) was treated as sufficient
to judge the *content* converged, declining the fifth reviewer's own
recommendation to switch to a full positional re-audit — a proportionate
call for a docs-only sweep, not a universal rule. The signal that mattered
wasn't a fixed round count; it was that each round's findings were a
different, narrower instance of the same known failure shape rather than a
new open-ended category.
