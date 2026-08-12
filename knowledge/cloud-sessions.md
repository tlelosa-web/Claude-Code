Findings about the Claude Code **remote/cloud execution environment** (web,
mobile, GitHub-triggered sessions) — the ephemeral container, its network
policy, and tooling quirks. Machine-specific findings for Operations and
Pappa T live in their own files.

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
Operations or Pappa T machine, or the GitHub web UI. Automation that runs
entirely in the cloud and needs to clean up branches after itself is blocked
at present.

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
