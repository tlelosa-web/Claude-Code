> **MOVED to `RMLRACE/pitwall-companion`, 2026-08-06 — do not work in
> `tlelosa-web/pitwall-companion` (deleted 2026-08-17).** This banner exists
> because an `INDEX.md` row alone did not stop a full day of feature work
> landing in the old location after the move (see the 2026-08-17 entry
> below) — read this line before starting any pitwall-companion work.

## 2026-08-17 — tlelosa-web/pitwall-companion was a stale fork; RMLRACE is sole canonical repo, tlelosa-web deleted
**Source:** session (RMLRACE-reconciliation task, triggered by a scheduled Discord-message reminder)
**Status:** active

The 2026-08-06 entry below already recorded the repo move
`tlelosa-web`→`RMLRACE`, but a full day of session work on 2026-08-06
through roughly 2026-08-16 (rename to "PitWall Companion", Loadouts By
Track + Suggested Boost, Boosts-ownership tab with custom-boost entry,
4 newly-identified boosts, GP Event availability filter, collapsible
New Boost form) happened against `tlelosa-web/pitwall-companion` anyway
— a session picked the stale fork back up without the INDEX.md pointer
being followed. Diff comparison (`RMLRACE/pitwall-companion` cloned
read-only, `tlelosa-web/pitwall-companion` HEAD at the time) confirmed
`RMLRACE` is a strict superset: 3,173 lines vs 2,560, `CACHE_VERSION
f1sheet-v22` vs `v11`, plus welcome/onboarding modal, per-card
GP-availability badges, Paddock Picks/Special-rarity collection (16
cards), a 23rd Legendary driver, custom-driver support, a Season-tab
scoring fix, and a schema 1→2 migration that `tlelosa-web` never got.
`RMLRACE` also already has Loadouts By Track, Suggested Boost, and a
more general collapsible-panel component (`.coll-summary`, covers both
the New Boost form and the GP filter panel, not just the one this
session built).

**Resolution:** owner (Tebello) confirmed `RMLRACE` is their own
gaming-projects org and is the one true copy going forward.
`tlelosa-web/pitwall-companion` is being deleted (manual step via
GitHub Settings → Danger Zone — no MCP tool deletes a whole repo).
Nothing from the 2026-08-06→08-16 `tlelosa-web` work needs to be
ported: every feature it added already exists in `RMLRACE`'s superset,
independently built. Going forward, **all pitwall-companion work must
target `RMLRACE/pitwall-companion`** — cross-org push needs a session
started with that repo as its initial source (`add_repo` with
`access:"push"` mid-session was tried and explicitly rejected:
"cross-tier adds are not supported in v1").

**Reusable lesson:** an INDEX.md line documenting a repo move is not
enough to stop a later session from working in the old location if
that session doesn't cross-check the org before starting feature work.
Worth a sharper flag (e.g. a first line in this file itself, not just
the index row) next time a repo relocates across orgs.

## 2026-08-06 — Same stale-PWA trap as CrateTracker; fix not applied here yet
**Source:** session (fix built and shipped in RMLRACE/cratetracker)
**Status:** active

`sw.js` is cache-first on the same pattern, so the same trap applies:
even with the cache version bumped, an installed PWA needs **two** opens
before a deploy is visible, and the first one reads as "the update didn't
ship". CrateTracker now prompts instead — full pattern (no `skipWaiting()`,
`SKIP_WAITING` postMessage, `controllerchange` reload guarded on whether a
controller existed at load, `reg.update()` on `visibilitychange`) is in the
2026-08-06 entry of `cratetracker.md`. **Not yet ported here** — worth
doing given this app has trusted testers who'd hit the same confusion.

## 2026-07-23 — What it is & structure
**Source:** tlelosa-web/pitwall-companion README.md
**Status:** active

"F1 Clash Resource Sheet" — offline-first, installable PWA tracking F1
Clash driver/component levels and card counts, replacing the community
"F1 Clash 2026 Resource Sheet v1.0/v1.1" (TR The Flash) with a live
tracker. No build step, no framework, no server — static files only
(`index.html`, `sw.js`, `manifest.webmanifest`, `icons/`). Public repo,
no sensitive data; nothing sent off-device (no accounts, no analytics,
no network calls at runtime).

Five tabs: Drivers, Parts, Tools (Suggested Drivers / Loadouts /
Compare, all computed live from owned cards — nothing stored), Season
(CC score dashboard, recomputed live), Rewards (read-only reference
tables). Covers all 88 driver cards and 46 components from the v1.1
workbook.

## 2026-07-23 — localStorage keys
**Source:** tlelosa-web/pitwall-companion README.md
**Status:** active

- `f1sheet.v1` — card level/count overrides, keyed by card id
  (`d:<Rarity>:<Name>` for drivers, `c:<Category>:<Name>` for
  components). Only *changed* values are stored, so seed-data updates
  still flow through untouched cards.
- `f1sheet.season.v1` — Season-tab inputs (dates, milestone counts).
- `f1sheet.boosted.v1` — per-card "Boosted +10%" toggles.
- Each key carries a `schema` field for safe future migrations.
- **Export/Import currently only covers `f1sheet.v1`** — Season inputs
  persist locally but aren't yet part of the backup file. Worth knowing
  before assuming a full-state export exists.

## 2026-07-23 — Cache-busting gotcha (shared with cratetracker)
**Source:** tlelosa-web/pitwall-companion README.md
**Status:** active

Service worker precaches the app for offline use. After changing any
cached file (`index.html`, `sw.js`, `manifest.webmanifest`, an icon),
bump `CACHE_VERSION` at the top of `sw.js` (e.g. `f1sheet-v1` →
`f1sheet-v2`) — otherwise installed devices keep serving the stale
cache even after a push.

## 2026-08-06 — Cache-busting gotcha actually missed three times in a row
**Source:** session (Spa track, Compare-tab Boosts, GP Event collapsible, PRs #18/#19)
**Status:** active

The 2026-07-23 rule above was documented but not followed: three
consecutive `index.html`-only PRs (#18's Spa/Compare-Boosts changes, #19's
GP Event collapsible) all shipped without bumping `CACHE_VERSION` — none
of those sessions checked `sw.js` before committing. Caught retroactively
in the PR #22 session (onboarding slideshow) and fixed with a single
catch-up bump (`f1sheet-v13` → `v14`) covering all four unbumped changes
at once, rather than trying to re-open the already-merged PRs. **Concrete
takeaway:** treat any `index.html`-touching commit as incomplete until
`sw.js`'s `CACHE_VERSION` has also been bumped in the same commit — don't
rely on remembering the rule from a knowledge-file read at session start;
check it at commit time, every time.

## 2026-07-23 — Modeling notes worth not re-deriving
**Source:** tlelosa-web/pitwall-companion README.md
**Status:** active

- "Boosted +10%" scales a card's positive stats and Total/Team Score by
  +10%, rounded — except **Pit Time**, which is left unscaled since it's
  a lower-is-better duration, not an additive stat.
- Loadouts (Tools tab) are **recomputed live from the user's own owned
  components** rather than embedding the source workbook's stale
  author-specific "Suggested Loadouts" grid.
- 65 distinct named Boosts after de-duplicating the source sheet's ~214
  rows (blank/header/repeated rows collapse out).
- The 22 Legendary drivers carry Series 0 in the source sheet (they
  unlock outside Series progression) — expected to show no Series badge.
