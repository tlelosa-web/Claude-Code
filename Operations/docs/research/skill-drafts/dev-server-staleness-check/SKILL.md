---
name: dev-server-staleness-check
description: Use before trusting any live/browser verification of a backend or full-stack code change — confirms the dev server process actually reloaded the new code rather than still serving a stale process. Trigger whenever you're about to verify a change (route, service/business logic, config, dependency bump) by hitting a running dev server (Flask, FastAPI, Next.js, Vite, Django, Rails, etc.) — especially anything beyond templates/CSS that a framework's hot-reload doesn't cover. Skip if only a template/CSS/pure-frontend-component edit was made and the server has a confirmed, working hot-reload path for that exact file type.
---

## Why this exists

A dev server that's still running from an earlier session or an earlier edit
will happily keep serving old code while looking completely healthy —
requests succeed, pages render, nothing errors. The bug (or the fix) looks
"not there" purely because the process never picked up the change, not
because the change is wrong. This is expensive precisely because it's
silent: it produces false confidence in exactly the step meant to catch
mistakes, on both bug reports ("I don't see it") and fix verification ("looks
fixed"). It recurs across virtually every framework — Werkzeug's reloader,
FastAPI/uvicorn's `--reload`, Vite's dev server, and Next.js's Turbopack/
webpack — because each has different rules for what triggers a full
restart vs. a hot patch.

## Steps

1. **Identify what actually needs to reload.** Classify the edit:
   - Full-process-restart required: route/handler code, service/business
     logic, environment variables, config files, new dependencies, schema
     changes, anything imported at module load time.
   - Usually hot-reloadable: templates, CSS, and (for frameworks with real
     HMR — Vite, webpack dev server, Next.js Fast Refresh) most UI
     component code.
   - When unsure which bucket an edit falls into for the framework in use,
     treat it as requiring a restart — the cost of an unnecessary restart is
     low; the cost of a false-negative verification is not.

2. **Check what's actually serving the port before trusting a check.**
   Find the process bound to the dev server's port and compare its start
   time against the most recently edited file's mtime (or the latest
   commit time, if using git). If the process started *before* the edit,
   it is stale — any check against it is meaningless.

3. **Don't kill a process you didn't start, without asking first.** A
   process already listening on the target port may belong to a different
   session, a different task, or the user themselves. Surface what you
   found (PID, start time, command line if available) and confirm before
   terminating it.

4. **If more than one process is listening on the same port**, treat that
   as a bug in its own right worth surfacing — not something to silently
   route around by picking one.

5. **Restart the correct process, wait for its "ready" signal**, then
   re-run the verification from a clean, freshly-started state — not from
   cached output of the earlier check.

## Evidence this pattern recurs

Confirmed independently across backend route/service changes, full-stack
verification workflows, and UI-only changes on different frameworks —
observed repeatedly across multiple unrelated projects' own histories, not
a one-off. If you're seeing "this looks unfixed" or "I can't reproduce the
bug that was reported" right after an edit, check this before anything
else.
