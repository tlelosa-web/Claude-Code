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
