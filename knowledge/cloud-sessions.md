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
