## 2026-08-05 — What it is, org, and status
**Source:** cloud session (this repo's PWA design + build)
**Status:** active

PitCrew Sync — third sibling F1 Clash companion PWA alongside
`cratetracker` and `pitwall-companion`, but the deliberate odd one out:
unlike those two (free, no monetization, static hand-baked data), PitCrew
Sync exists specifically to let Tebello take **compensation** via an
optional Ko-fi donation, and its driver/component reference data is
**spreadsheet-synced** by the user rather than hand-transcribed into the
code. Repo: `RMLRACE/pitcrew-sync` (not `tlelosa-web` — a different org
than the other two sibling apps, created directly by Tebello via the
GitHub UI after this session's own `create_repository` MCP call 403'd).
Public, GitHub Pages-hosted, same flat/no-build/single-`index.html`
architecture as the siblings.

Live app: `https://rmlrace.github.io/pitcrew-sync/`.

## 2026-08-05 — Data model, sync, and sharing
**Source:** cloud session
**Status:** active

Generic catalog, not a fixed card list like PitWall Companion's baked-in
88 drivers/46 components — each catalog row is `{id, name, category,
rarity, targetLevel, targetCount}`, sourced from whatever CSV the user
points the app at (`Sync` tab: paste a Google Sheets "Publish to web ->
CSV" URL, or a normal share URL which the app auto-rewrites to the CSV
export endpoint). Sync is atomic — a bad fetch or malformed sheet never
overwrites existing data. `localStorage` keys: `pitcrewsync.catalog.v1`,
`pitcrewsync.progress.v1` (per-card level/count), `pitcrewsync.settings.v1`
(sync URL + last-sync info). Ships with an **empty** bundled catalog by
design (no default spreadsheet prefilled) — sidesteps needing consent from
any specific spreadsheet author, but means a brand-new user sees "No cards
yet" until they either sync one or import a backup.

Export/import is a plain JSON file (`pitcrew-sync-backup-<date>.json`),
same device-local "sharing" philosophy as both siblings — no P2P, no
backend, no accounts.

**Bootstrap-from-PitWall-Companion converter** (Backup tab, added this
session, user-requested and tested with the user's own real export as the
target verification step): reads a PitWall Companion backup JSON
(`{overrides:{"d:<Rarity>:<Name>":{level,amount}, ...}}`), decodes each
override id, and merges into PitCrew Sync's catalog+progress — additive,
never clobbers existing catalog metadata for ids that already exist (e.g.
from a real spreadsheet sync), only updates their progress. PitWall
Companion's export only ever contains cards the user actually leveled
there (no full roster, no cost/cap/target data), so this seeds a partial
catalog, not a substitute for a real spreadsheet sync.

## 2026-08-05 — Visual identity mismatch (found + fixed)
**Source:** cloud session
**Status:** active

The app was originally built (functionally) by one cloud session, then
independently restyled/pushed by a second session that gave it its own
CSS — orange (`#ff6b35`) brand color, emoji logo, no install button, no
search/filter UI, no rarity-color badges. Tebello opened the live app and
flagged it as looking nothing like the two sibling apps. A follow-up
session restyled it to match: F1-red (`#e10600`, same value as PitWall
Companion) accent, real logo image + install button + sticky-blur header
(PitWall's 3-column grid pattern), pill-container tab bar with red active
state, added search bar + category filter-chip row (new — PitCrew Sync
had neither), and deterministic rarity-badge coloring for arbitrary
spreadsheet strings (known F1-Clash values map to PitWall's actual hues;
anything else hashes into the same small palette so it's still stable and
on-brand). Fixed a related fragility surfaced by the new search feature:
the Cards-tab step-button listener was rebound with `{once:true}` on every
`render()`, which a search-triggered re-render (bypassing
`wireTabContent()`) would have silently dropped — now a persistent
delegated listener on `#app`.

Lesson for future work here: **screenshot-check the live app against its
siblings before considering a build "done"** — the functional build was
solid on first pass, but nobody had actually looked at it next to
`cratetracker`/`pitwall-companion` until Tebello did.

## 2026-08-05 — Push-access gotcha: `RMLRACE` org not in this session's grant
**Source:** cloud session
**Status:** active

Unlike `tlelosa-web` repos (which this session type has native push access
to), `RMLRACE/pitcrew-sync` required an explicit `add_repo(access: push)`
grant that got stuck in a "requires approval" loop for most of this
session, then was ultimately **denied** when a real approval prompt
finally surfaced. Read access to the public repo worked fine the whole
time via the session's git proxy (clone/fetch), so two full builds (the
PitWall-import converter, then the F1-red restyle) got made and committed
locally but couldn't be pushed. Resolved by generating `git format-patch`
files and handing them to Tebello to `git am` + push from his own machine
— those two commits (PitWall-import bootstrap, F1-red restyle) may or may
not be on `origin/main` yet depending on whether/when Tebello applied
them. **Check `git log origin/main` before assuming either feature is
live** — don't rebuild them from scratch if they're just sitting in a
patch file waiting to be applied.
