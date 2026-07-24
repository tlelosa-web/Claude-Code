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
**Status:** active

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
