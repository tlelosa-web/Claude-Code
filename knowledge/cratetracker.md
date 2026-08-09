## 2026-08-06 — Cache-busting isn't enough: the SW update prompt
**Source:** session (RMLRACE/cratetracker PRs #8, #9)
**Status:** active

Bumping `CACHE_VERSION` is necessary but was never sufficient, and the
gap cost a whole debugging round. With the old cache-first worker a
deploy needed **two** app opens to appear: the first still served the
stale shell while the browser byte-diffed `service-worker.js`, installed
the new worker and cached the new shell; only the second load served it.
So a change that merged and deployed green still looked "not live" on
device — check this before assuming the deploy failed.

The worker now parks rather than self-activating, and the page offers the
update:

- `service-worker.js` — **no `skipWaiting()` in `install`**. A new worker
  stays in *waiting* instead of swapping the app out mid-race-log, and
  activates on a `{type:'SKIP_WAITING'}` `postMessage` from the page.
  First installs are unaffected: with no active worker it activates
  immediately anyway.
- `index.html` — a bottom toast ("New version available" · Update ·
  dismiss) wired both to `updatefound` **and** to `reg.waiting`, which
  catches a worker left waiting by an earlier visit. Update posts
  `SKIP_WAITING`; `controllerchange` then reloads once.
- **Guard that reload** on whether `navigator.serviceWorker.controller`
  existed *at load time*. `clients.claim()` fires `controllerchange` on a
  first install too, and without the guard a first-time visitor gets
  reloaded for no reason.
- `reg.update()` on `visibilitychange` — a home-screen PWA can stay open
  for days and never cold-start, so a load-time-only check rarely fires.

Still bump `CACHE_VERSION` on every `index.html`/icon change: the byte
change to `service-worker.js` is what makes the browser notice at all.
Confirmed working against a real deploy on 2026-08-06.

## 2026-08-06 — Race count ≠ win count (the two header badges)
**Source:** session (RMLRACE/cratetracker PRs #7, #10)
**Status:** active

`computeSeries()` derives two different numbers per logged entry and they
deliberately diverge — neither is `state.entries.length`:

- **`win`** — the in-game win counter (`startWin + entries`). *Every*
  logged entry increments it, including GP/event races and back-to-back
  Goldens. Shown in the 🏆 header pill.
- **`race`** — position in the crate cycle. GP/event races and a Golden
  immediately following a Golden do **not** increment it. Shown in the 🏁
  pill and the "Race N / 14" step-progress bar.

They also reset differently: `race` restarts at 0 on every step advance
(`handleSetBaseline()` clears `state.entries`), while `win` carries
forward because that same function moves `startWin` up to the win where
the premium landed. So the 🏆 badge reads `rows.at(-1).win`, falling back
to `state.startWin` before anything is logged — no extra counter state is
needed. A naive "count the button presses" tally is wrong: it read 1 on a
save sitting at win 2497.

## 2026-08-06 — State shape and where the displayed numbers come from
**Source:** session (RMLRACE/cratetracker `index.html`)
**Status:** active

One file, no framework, no build — vanilla DOM with template-string
`innerHTML`, rendered by `renderAll()` after every mutation. State is a
single object persisted whole to `localStorage` under
`f1clash_crate_tracker_v2`:

`{ startWin, entries, activeStep, baselineType }`

`entries` is just an array of crate-type strings (`s|g|p|l|gp|f`) for the
**current step only** — `handleSetBaseline()` clears it on every advance,
so there is no cross-step history and no lifetime stats can be derived
from it. Every displayed number is recomputed from `entries` by
`computeSeries()` on each render; no counters are stored. `STEP_RC` holds
the target race count per step (`[14,26,21,40,32,48,27,32]`). There is no
URL/share import path that writes state, so `loadState()` is the only
place a new field needs a default.

## 2026-07-23 — What it is & structure
**Source:** tlelosa-web/cratetracker README.md
**Status:** active

Single-purpose, offline-first PWA that predicts the premium crate cycle
in the mobile game **F1 Clash**. Ported from the community spreadsheet
"Track & find Premium Crates" by TR The Flash. No build step — static
files only: `index.html` (app), `manifest.json`, `service-worker.js`,
icons, `.nojekyll`. All user data (baseline, race log, active step)
stays in `localStorage` — nothing leaves the device. Public repo, no
sensitive data.

Deploy: push to `main`, enable GitHub Pages (Settings → Pages → Deploy
from a branch → `main` / root). `.nojekyll` is required so `icons/` and
other paths serve verbatim.

## 2026-07-23 — Cache-busting gotcha (shared with pitwall-companion)
**Source:** tlelosa-web/cratetracker README.md
**Status:** superseded — see the 2026-08-06 SW update-prompt entry above.
The bump is still required, but on its own it left users a deploy behind.

The service worker caches aggressively for offline use — browsers keep
serving the old version until the cache is explicitly invalidated. After
editing `index.html` or any cached file, bump the version string in
`service-worker.js` (e.g. `cratetracker-v1` → `cratetracker-v2`), then
commit/push. Without the bump, installed devices keep the stale cache
indefinitely.

## 2026-07-23 — Crate-cycle model
**Source:** tlelosa-web/cratetracker README.md
**Status:** active

Per-race crate pattern for all 8 steps is read from the source
spreadsheet's conditional formatting, encoded in `index.html`
(`STEP_GOLDS` / `STEP_RC`). Two steps carry advisory (not auto-applied)
notes because they depend on live in-game timing the app can't observe:
Step 1 (Platinum may land race 13 or 14), Step 3 (every third cycle adds
a bonus Golden at race 9, shifting later crates one race later).
