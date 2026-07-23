# Build Prompt — F1 Clash Resource Sheet (mobile PWA)

> Paste everything below the line into a **fresh** Claude Code session, working in a **new, empty repository** you have already created (named e.g. `f1clash-companion`). It is fully self-contained — the seed data is included, so no access to the original Google Sheet is needed.
>
> **Note on repo creation:** creating the GitHub repo itself may need to be done by you in the GitHub UI — an automated integration can hit `403 Resource not accessible by integration`. Create the empty repo first, then run this prompt against it.

---

## Role & objective

Build **F1 Clash Resource Sheet**, a small, **offline-first** Progressive Web App (PWA) that turns the community *F1 Clash 2026 Resource Sheet (v1.0 by TR The Flash)* into a phone-installable tracker for **driver and component levels and card counts**. It must install to a home screen, work fully offline after first load, keep all data on-device, and need no build step or server. Ship as static files served from the repo root via GitHub Pages.

## Hard constraints

1. **No build tooling, framework, or bundler.** Plain HTML + CSS + JS.
2. **No runtime network dependencies.** No CDNs, web fonts, analytics, or remote APIs. Must load and work with the network disabled.
3. **One `index.html`** with inline `<style>` and `<script>` (seed data embedded in the script). Only other runtime files: service worker, manifest, icons, `.nojekyll`.
4. **All state in `localStorage`** under a namespaced key. Nothing leaves the device.
5. **Offline via a service worker** that precaches every file needed to run.

## Deliverables (file list)

```
index.html                 # app: markup + inline CSS + inline JS (with seed data)
sw.js                      # service worker: precache + offline fallback
manifest.webmanifest       # PWA manifest (standalone, icons, theme)
icons/icon-192.png         # maskable-safe, 192x192
icons/icon-512.png         # maskable-safe, 512x512
icons/apple-touch-icon.png # 180x180
.nojekyll                  # GitHub Pages serves paths verbatim
README.md                  # what it is, run, deploy, cache-busting note
```

Generate simple flat icons (a white crate/box glyph on F1-red `#e10600`), no network fetches.

## Features

- Two tabs: **Drivers** and **Components**.
  - Drivers grouped by rarity: **Common, Rare, Epic, Legendary**.
  - Components grouped by category: **Front Wing, Brakes, Suspension, Rear Wing, Gearbox, Engine, Battery**.
- Each card shows: name, a rarity badge, a **Level** with −/+ steppers, and an **editable card count** (numeric input).
- A progress bar toward the next level using the cost table below; show **★ MAX** when a card is at its rarity cap.
- **Search** box (filter by name) and **filter chips** (All + each group of the active tab).
- **Export** / **Import** a JSON backup, and **Reset** to the built-in seed defaults (with confirm).
- **Install** button wired to `beforeinstallprompt`; runs standalone once installed; **dark mode by default** honoring `prefers-color-scheme`.

## Rules / constants

```js
// card cost to reach the NEXT level, keyed by current level
const COST = {1:4,2:10,3:20,4:50,5:100,6:200,7:400,8:1000,9:2000,10:4000,11:8000};
// max level per rarity (Rare caps at 9; adjust if the game changes)
const CAP  = {Common:11, Rare:9, Epic:7, Legendary:5};
```

Progress toward next level = `min(amount / COST[level], 1)`; at `level >= CAP[rarity]` show `★ MAX` instead of a bar.

## Data model (localStorage)

- Key `f1sheet.v1` → `{ schema:1, overrides:{ "<id>": {level, amount} }, savedAt }`.
- `id` format: `d:<Rarity>:<Name>` for drivers, `c:<Category>:<Name>` for components.
- Only store cards whose level/amount differ from the seed defaults (overrides), so future seed updates still flow through. Include a `schema` guard for safe future migrations.

## Mobile-first UX

- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`; respect `env(safe-area-inset-*)`.
- Sticky header (title + search + tabs); horizontally scrollable filter chips.
- Tap targets ≥ 40px; no hover-only affordances; no horizontal page scroll; visible pressed feedback.
- `theme_color`/`background_color` = `#0b0f1a`; standalone display; readable contrast (WCAG AA).

## PWA requirements

- `manifest.webmanifest`: `name`, `short_name`, `start_url:"./"`, `scope:"./"`, `display:"standalone"`, colors, and icons (192 + 512, plus one `"purpose":"maskable"`).
- iOS: `apple-mobile-web-app-capable`, status-bar style, and `apple-touch-icon` link.
- `sw.js`: single `CACHE_VERSION` constant; precache `./`, `index.html`, manifest, icons on install; cache-first with network fallback to `index.html`; delete old caches on activate. Register with a **relative** path so it works under `/<repo>/` on Pages. Use relative URLs throughout.

## Acceptance criteria

1. Loads and is fully usable offline after first visit.
2. Installable on Android Chrome and iOS "Add to Home Screen"; launches standalone with the correct icon/theme.
3. Editing a level or card count persists across reloads; Export/Import/Reset all work.
4. Maxed Rare cards (level 9) show ★ MAX; others show a correct "to next level" bar.
5. No runtime requests to any external host.

## Deployment (document in README)

1. Commit all files to the repo root.
2. Settings → Pages → Deploy from branch → **main / (root)**.
3. Keep `.nojekyll` present. Note: private repos need GitHub Pro for Pages — otherwise make the repo public or host on any static host.
4. Bump `CACHE_VERSION` in `sw.js` whenever a cached file changes.

## Seed data

Embed this object into the script as `const DEFAULT = {…}`. Levels and card counts reflect a recent snapshot (drivers by rarity; components by category). Legendary drivers were not captured and are left at their sheet values.

```json
{
  "drivers": {
    "Common": [
      {
        "name": "Lindblad",
        "rarity": "Common",
        "level": 7,
        "amount": 2397
      },
      {
        "name": "Colapinto",
        "rarity": "Common",
        "level": 7,
        "amount": 2612
      },
      {
        "name": "Bottas",
        "rarity": "Common",
        "level": 7,
        "amount": 3131
      },
      {
        "name": "Bortoleto",
        "rarity": "Common",
        "level": 8,
        "amount": 1866
      },
      {
        "name": "Gasly",
        "rarity": "Common",
        "level": 6,
        "amount": 2647
      },
      {
        "name": "Stroll",
        "rarity": "Common",
        "level": 6,
        "amount": 3753
      },
      {
        "name": "Ocon",
        "rarity": "Common",
        "level": 6,
        "amount": 2952
      },
      {
        "name": "Lawson",
        "rarity": "Common",
        "level": 7,
        "amount": 1938
      },
      {
        "name": "Bearman",
        "rarity": "Common",
        "level": 8,
        "amount": 1326
      },
      {
        "name": "Hadjar",
        "rarity": "Common",
        "level": 9,
        "amount": 1104
      },
      {
        "name": "Hulkenberg",
        "rarity": "Common",
        "level": 6,
        "amount": 3067
      },
      {
        "name": "Alonso",
        "rarity": "Common",
        "level": 5,
        "amount": 2055
      },
      {
        "name": "Sainz",
        "rarity": "Common",
        "level": 5,
        "amount": 3208
      },
      {
        "name": "Albon",
        "rarity": "Common",
        "level": 5,
        "amount": 2631
      },
      {
        "name": "Antonelli",
        "rarity": "Common",
        "level": 5,
        "amount": 2912
      },
      {
        "name": "Perez",
        "rarity": "Common",
        "level": 5,
        "amount": 2890
      },
      {
        "name": "Hamilton",
        "rarity": "Common",
        "level": 4,
        "amount": 2544
      },
      {
        "name": "Leclerc",
        "rarity": "Common",
        "level": 4,
        "amount": 2604
      },
      {
        "name": "Russell",
        "rarity": "Common",
        "level": 4,
        "amount": 2230
      },
      {
        "name": "Piastri",
        "rarity": "Common",
        "level": 3,
        "amount": 2143
      },
      {
        "name": "Verstappen",
        "rarity": "Common",
        "level": 4,
        "amount": 2262
      },
      {
        "name": "Norris",
        "rarity": "Common",
        "level": 3,
        "amount": 1943
      }
    ],
    "Rare": [
      {
        "name": "Bortoleto",
        "rarity": "Rare",
        "level": 9,
        "amount": 0
      },
      {
        "name": "Bottas",
        "rarity": "Rare",
        "level": 9,
        "amount": 0
      },
      {
        "name": "Colapinto",
        "rarity": "Rare",
        "level": 6,
        "amount": 1352
      },
      {
        "name": "Lindblad",
        "rarity": "Rare",
        "level": 2,
        "amount": 908
      },
      {
        "name": "Gasly",
        "rarity": "Rare",
        "level": 2,
        "amount": 900
      },
      {
        "name": "Stroll",
        "rarity": "Rare",
        "level": 2,
        "amount": 1061
      },
      {
        "name": "Ocon",
        "rarity": "Rare",
        "level": 1,
        "amount": 421
      },
      {
        "name": "Lawson",
        "rarity": "Rare",
        "level": 1,
        "amount": 321
      },
      {
        "name": "Bearman",
        "rarity": "Rare",
        "level": 6,
        "amount": 283
      },
      {
        "name": "Hadjar",
        "rarity": "Rare",
        "level": 1,
        "amount": 520
      },
      {
        "name": "Hulkenberg",
        "rarity": "Rare",
        "level": 1,
        "amount": 342
      },
      {
        "name": "Alonso",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Sainzz",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Albon",
        "rarity": "Rare",
        "level": 1,
        "amount": 29
      },
      {
        "name": "Antonelli",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Perez",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Hamilton",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Leclerc",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Russell",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Piastri",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Verstappen",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Norris",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      }
    ],
    "Epic": [
      {
        "name": "Gasly",
        "rarity": "Epic",
        "level": 6,
        "amount": 148
      },
      {
        "name": "Lindblad",
        "rarity": "Epic",
        "level": 7,
        "amount": 96
      },
      {
        "name": "Bottas",
        "rarity": "Epic",
        "level": 6,
        "amount": 183
      },
      {
        "name": "Colapinto",
        "rarity": "Epic",
        "level": 6,
        "amount": 49
      },
      {
        "name": "Lawson",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Bortoleto",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Stroll",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Ocon",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Hulkenberg",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Albon",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Perez",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Bearman",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Hadjar",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Alonso",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Sainz",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Antonelli",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Hamilton",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Leclerc",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Russell",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Piastri",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Verstappen",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Norris",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Legendary": [
      {
        "name": "Fisichella",
        "rarity": "Legendary",
        "level": 2,
        "amount": 43
      },
      {
        "name": "McLaren",
        "rarity": "Legendary",
        "level": 3,
        "amount": 100
      },
      {
        "name": "G.Villeneuve",
        "rarity": "Legendary",
        "level": 1,
        "amount": 29
      },
      {
        "name": "Webber",
        "rarity": "Legendary",
        "level": 2,
        "amount": 0
      },
      {
        "name": "Berger",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Massa",
        "rarity": "Legendary",
        "level": 2,
        "amount": 3
      },
      {
        "name": "Coulthard",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Rindt",
        "rarity": "Legendary",
        "level": 1,
        "amount": 10
      },
      {
        "name": "Hunt",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "J.Villeneuve",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Andretti",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Button",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "D.Hill",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Mansell",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "G.Hill",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Fittipaldi",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Lauda",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Brabham",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Fangio",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Prost",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Schumacher",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Senna",
        "rarity": "Legendary",
        "level": 0,
        "amount": 0
      }
    ]
  },
  "components": {
    "Front Wing": [
      {
        "name": "Wind Guard",
        "rarity": "Common",
        "level": 9,
        "amount": 1049
      },
      {
        "name": "Zephyr",
        "rarity": "Rare",
        "level": 9,
        "amount": 836
      },
      {
        "name": "Laminar",
        "rarity": "Common",
        "level": 9,
        "amount": 1181
      },
      {
        "name": "Scythe",
        "rarity": "Common",
        "level": 8,
        "amount": 2010
      },
      {
        "name": "Flashpoint",
        "rarity": "Epic",
        "level": 6,
        "amount": 29
      },
      {
        "name": "Leading Edge",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Loose Fit",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Brakes": [
      {
        "name": "Anchor",
        "rarity": "Common",
        "level": 9,
        "amount": 537
      },
      {
        "name": "Flow 2K",
        "rarity": "Common",
        "level": 9,
        "amount": 805
      },
      {
        "name": "Aegis",
        "rarity": "Common",
        "level": 6,
        "amount": 2602
      },
      {
        "name": "Scramble",
        "rarity": "Rare",
        "level": 8,
        "amount": 350
      },
      {
        "name": "Aura Lock",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Pressure Point",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Stabilix",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Suspension": [
      {
        "name": "Shockwave",
        "rarity": "Common",
        "level": 9,
        "amount": 1221
      },
      {
        "name": "Jumpstart",
        "rarity": "Common",
        "level": 9,
        "amount": 948
      },
      {
        "name": "Stability Unit",
        "rarity": "Common",
        "level": 9,
        "amount": 845
      },
      {
        "name": "Equilibrium",
        "rarity": "Rare",
        "level": 8,
        "amount": 815
      },
      {
        "name": "Curver 3.0",
        "rarity": "Epic",
        "level": 5,
        "amount": 8
      },
      {
        "name": "Motion Link V2",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Bounce",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Rear Wing": [
      {
        "name": "Wobble",
        "rarity": "Rare",
        "level": 9,
        "amount": 502
      },
      {
        "name": "Tailwind",
        "rarity": "Common",
        "level": 9,
        "amount": 1222
      },
      {
        "name": "Air Channel",
        "rarity": "Common",
        "level": 9,
        "amount": 2577
      },
      {
        "name": "Vibe Lift",
        "rarity": "Common",
        "level": 8,
        "amount": 1830
      },
      {
        "name": "Impact",
        "rarity": "Rare",
        "level": 7,
        "amount": 8
      },
      {
        "name": "Downforce",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Dominus",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Gearbox": [
      {
        "name": "Cadence",
        "rarity": "Common",
        "level": 9,
        "amount": 741
      },
      {
        "name": "Flow Logic",
        "rarity": "Common",
        "level": 9,
        "amount": 1135
      },
      {
        "name": "Stratos",
        "rarity": "Epic",
        "level": 7,
        "amount": 24
      },
      {
        "name": "Shift X",
        "rarity": "Rare",
        "level": 8,
        "amount": 190
      },
      {
        "name": "Lockdown",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Fracture",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Powerbox",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Engine": [
      {
        "name": "Tempest",
        "rarity": "Epic",
        "level": 7,
        "amount": 35
      },
      {
        "name": "Bedrock",
        "rarity": "Common",
        "level": 9,
        "amount": 1358
      },
      {
        "name": "Velocity",
        "rarity": "Common",
        "level": 8,
        "amount": 1670
      },
      {
        "name": "Axis 3000",
        "rarity": "Rare",
        "level": 8,
        "amount": 153
      },
      {
        "name": "DriveOS",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Hotfix",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Overdrive",
        "rarity": "Epic",
        "level": 0,
        "amount": 0
      }
    ],
    "Battery": [
      {
        "name": "Charge Core",
        "rarity": "Epic",
        "level": 6,
        "amount": 188
      },
      {
        "name": "Power Grid",
        "rarity": "Common",
        "level": 6,
        "amount": 1088
      },
      {
        "name": "Energy Reserve",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      },
      {
        "name": "Spare Pack",
        "rarity": "Rare",
        "level": 0,
        "amount": 0
      }
    ]
  }
}
```
