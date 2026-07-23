# Build Prompt — "Crate Timer" mobile-friendly PWA

> Paste everything below the line into Claude Code (or your agent of choice), pointed at a **brand-new, empty repository**. It is self-contained. Reference app for look-and-feel and architecture: `tlelosa-web/cratetracker` (an offline-first, single-file F1 Clash crate-cycle PWA).

---

## Role & objective

You are building **Crate Timer**, a small, offline-first Progressive Web App (PWA) that helps a player track and predict in-game "crate" timers (built with F1 Clash's premium-crate cycle in mind, but keep the crate definitions in one clearly-marked config block so they're easy to change).

The app must be **installable to a phone home screen**, **work fully offline after first load**, keep **all data on-device**, and require **no build step and no server**. It ships as static files served by **GitHub Pages** from the repository root.

## Hard constraints (do not violate)

1. **No build tooling, no framework, no bundler.** Plain HTML + CSS + JavaScript only.
2. **No external network dependencies at runtime.** No CDNs, web fonts, analytics, or remote APIs. Everything needed to run is in the repo and cached. The app must load and function with the network fully disabled.
3. **Single-page app in one `index.html`** with CSS in a `<style>` block and JS in a `<script>` block (inline, no external `.css`/`.js` app files). The only other runtime files are the service worker, the manifest, icons, and `.nojekyll`.
4. **All state lives in `localStorage`.** Nothing leaves the device. No accounts, no cookies, no telemetry.
5. **Offline-capable via a service worker** that precaches every file needed to run.

## Deliverables (exact file list)

```
index.html                 # the entire app: markup + <style> + <script>
sw.js                      # service worker: precache + offline fetch handler
manifest.webmanifest       # PWA manifest (name, icons, standalone, theme)
icons/icon-192.png         # maskable-safe app icon, 192x192
icons/icon-512.png         # maskable-safe app icon, 512x512
icons/apple-touch-icon.png # 180x180 for iOS home screen
.nojekyll                  # so GitHub Pages serves files/paths verbatim
README.md                  # what it is, how to run, how to deploy, cache-busting note
```

If you generate the PNG icons programmatically, keep them tiny and simple (a flat crate glyph on a solid background). Do not pull icons from the internet.

## Core features

1. **Crate list / dashboard (home screen)**
   - Shows each tracked crate as a card: crate name, type/rarity, a live **countdown** to "ready", and a progress bar.
   - Cards sort by soonest-ready first. A crate that is ready shows a clear "READY" state (color + label) and, optionally, a buzz/notification.
   - Live countdowns tick every second and are computed from stored timestamps (so they stay correct across reloads and while offline).

2. **Add / edit / delete a crate timer**
   - Add a crate by choosing a type from the config (or custom), which sets its unlock duration; start the timer now or at a chosen time.
   - Edit duration/label; delete with confirm. Swipe or a clear button — keep touch targets ≥ 44px.

3. **Crate-cycle prediction (the "smart" part — mirror CrateTracker's model)**
   - Encode the crate cycle as data: an ordered set of **8 progression steps**. Each step defines which crate appears at each position — **Golden** races are explicitly defined; **Standard** crates fill intermediate positions; **premium** crates (**Platinum** / **Legendary**) appear at fixed step distances.
   - Handle the two documented special cases: **Step 1's Platinum position varies** slightly based on live in-game factors (expose it as an adjustable input), and **Step 3 can add bonus Golden crates** that shift the crates after it.
   - Track a **baseline**, a **race log**, and the **active step** in `localStorage`; use them to predict when the next premium crate is due and surface a "next premium in N races / ~time" readout.
   - Keep all cycle constants in a single, well-commented `CONFIG` object at the top of the script so the ruleset can be tuned without hunting through code.

4. **Race log & baseline reset**
   - Let the user log races (increment through the cycle), see current step, and **reset baseline** to re-sync with the game. Confirm destructive resets.

5. **Notifications (progressive enhancement)**
   - If the user grants permission, fire a local notification when a crate becomes ready. Degrade gracefully (in-app banner + optional vibration) when notifications are unavailable — never block core use on them.

## Mobile-first UX requirements

- Responsive layout that targets phones first; usable one-handed. Fluid widths, `max-width` container on larger screens.
- Respect the notch/safe areas: `viewport-fit=cover` + `env(safe-area-inset-*)` padding.
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.
- **Dark mode by default**, honoring `prefers-color-scheme`; readable contrast (WCAG AA).
- Big tap targets, no hover-only affordances, no horizontal scroll. Buttons give visible pressed feedback.
- Runs in **standalone** mode (no browser chrome) once installed; set an appropriate `theme-color`.
- Snappy: first paint under a second on a mid-range phone; no layout shift as countdowns tick.

## PWA requirements

- **`manifest.webmanifest`**: `name`, `short_name`, `start_url: "./"`, `scope: "./"`, `display: "standalone"`, `background_color`, `theme_color`, and `icons` (192 + 512, at least one `"purpose": "any maskable"`).
- Link the manifest and `apple-touch-icon`, and include the iOS meta tags (`apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`).
- **`sw.js`**: precache `index.html`, `manifest.webmanifest`, and the icons on `install`; serve cache-first with a network fallback; clean up old caches on `activate`.
- Use a **single `CACHE_VERSION` constant** in `sw.js`. Document in the README that any change to cached files requires bumping this version so clients refresh. Register the SW with a relative path so it works under a GitHub Pages project subpath (`/<repo>/`).
- Use **relative URLs** everywhere (`./…`) so the app works when hosted at `https://<user>.github.io/<repo>/`.

## Data model (localStorage)

Namespace keys under `crateTimer.*`. Store JSON. Suggested shape:

- `crateTimer.timers` → array of `{ id, label, type, startedAt, durationMs }`.
- `crateTimer.cycle` → `{ baselineStep, activeStep, raceLog: [...], step1PlatinumOffset, step3BonusGolden }`.
- `crateTimer.settings` → `{ notificationsEnabled, theme }`.
- `crateTimer.schemaVersion` → integer; write a tiny migration guard so future changes don't corrupt old data.

## Accessibility & quality

- Semantic HTML, labelled controls, focus-visible styles, `aria-live` on the countdown/next-premium readouts.
- No console errors. Guard every `localStorage`/Notification/SW call for unsupported or private-mode browsers.
- Keep the whole thing lightweight and dependency-free; comment the cycle logic clearly.

## Acceptance criteria (verify before finishing)

1. Loads and is fully usable with the network disabled after the first visit.
2. Passes an install prompt on Android Chrome and "Add to Home Screen" on iOS Safari; launches standalone with the correct icon and theme color.
3. Countdowns remain accurate across reloads and after being backgrounded (recomputed from timestamps, not intervals).
4. Adding, editing, and deleting a crate persists across reloads.
5. The cycle predictor advances through the 8 steps, honors the Step 1 and Step 3 special cases, and shows a correct "next premium" estimate for a sample baseline.
6. All data clears cleanly via a "reset" action and survives a `schemaVersion` bump.
7. No runtime requests to any external host (check the network panel).

## Deployment (do this and document it in the README)

1. Commit all files to the repo root of the new repository.
2. In repo **Settings → Pages**, deploy from the **main** branch, **/(root)** folder.
3. Confirm `.nojekyll` is present so paths/files serve verbatim.
4. Verify the live URL installs and runs offline on a phone.
5. README must explain the cache-busting step: bump `CACHE_VERSION` in `sw.js` whenever cached files change.

## Notes for the implementer

- Prioritize correctness of the timer math and the cycle model over visual flourish.
- Keep everything in as few files as the deliverable list allows; the reference app is deliberately a single self-contained HTML file plus SW/manifest/icons.
- Leave the crate/cycle definitions in one clearly-marked `CONFIG` block so the game's ruleset can be updated later without refactoring.
