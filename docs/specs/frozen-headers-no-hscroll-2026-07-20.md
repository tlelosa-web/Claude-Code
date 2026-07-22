# Frozen List Headers + No Horizontal Scroll (SO/WO/STO/PO Lists)

**Status:** Approved — ready for build
**Date:** 2026-07-20
**Batch:** 35
**Owner:** Tebello Lelosa
**Scope decisions:** confirmed via AskUserQuestion, 2026-07-20 (all three
recommended options accepted).

## Background — the bug that triggered this

Tebello reported PO3839 "missing" from the Purchase Orders list. Root cause
(diagnosed live in Tebello's own Chrome, 2026-07-20):

- `static/js/resizable_columns.js` sets `position: sticky` inline on every
  list-table `<th>` (Batch 31), and `static/css/main.css:324` gives
  `.data-table th` a `top: var(--topbar-height)` (56px) offset intended to
  make headers stick below the topbar **when the page scrolls**.
- But each list table is wrapped in `<div style="overflow-x: auto;">`. That
  wrapper — not the page — is the sticky elements' nearest scroll container,
  so the 56px offset is interpreted **relative to the wrapper**.
- When the wrapper genuinely overflows horizontally (Tebello's persisted
  column widths total 1,751px on the PO list vs a ~1,280px card), Chromium
  *paints* the header row 56px below its layout position. The header's
  opaque background then covers the first data row. Geometry APIs
  (`getBoundingClientRect`) still report the layout position — the paint
  and the layout disagree, which is why this never showed up in DOM checks.
- Whichever row sorts first is hidden. On the PO list PO3839 is first under
  both the default due-date sort and a PO-number sort — hence "missing".
- Two compounding findings: (1) the sticky headers have **never actually
  stuck** on page scroll in Chromium, because `position: sticky` on `th` is
  inert inside a `border-collapse: collapse` table (known Chromium
  limitation) *and* the overflow wrapper scopes the sticky to the wrong
  scrollport anyway; (2) the same latent bug exists on all 4 list pages —
  Tebello's browser also has saved Sales Orders widths that overflow,
  including one column dragged to 3px.

## Goal

1. **Frozen headers that actually work:** when a long list page scrolls,
   the column headers (labels + filter inputs) stick just below the topbar
   and stay visible. Page-level scrolling only — no new inner scrollbars.
2. **No horizontal scroll on the 4 list pages:** the table always fits the
   card width, at load and after any column resize. This removes the
   overflow wrapper that both caused the paint bug and made the 56px offset
   wrong — fixing the hidden-first-row bug at its root.

## Confirmed design decisions (Tebello, 2026-07-20)

1. **Freeze style:** headers freeze below the topbar as the page scrolls
   (not an inner scrollable table area).
2. **Resize model:** zero-sum — dragging a column border widens that column
   and narrows its right-hand neighbour by the same amount; total table
   width never changes, so overflow is impossible by construction.
3. **Existing saved widths:** scale-to-fit on load — proportionally rescale
   persisted widths to exactly fill the card, with a sane per-column
   minimum (fixes the 3px column). Do not discard user customization.

## Scope

**In scope (files):**

1. `static/css/main.css`
2. `static/js/resizable_columns.js`
3. `templates/sales_orders/list.html` (line ~26)
4. `templates/works_orders/list.html` (line ~17)
5. `templates/stock_orders/list.html` (line ~17)
6. `templates/purchase_orders/list.html` (line ~19)
7. `tests/test_resizable_columns.py`

**Out of scope:** every other `overflow-x: auto` wrapper in the codebase
(detail/edit/upload/dashboard/BOM pages — none of them are sticky or
resizable, none exhibit the bug); Tabulator pages (Items, Reports); print
templates; `static/js/table_sort_filter.js` (composes via the same `<th>`
DOM and needs no change — verify, don't modify).

## Design

### 1. CSS (`static/css/main.css`)

- `.data-table`: change `border-collapse: collapse` →
  `border-collapse: separate; border-spacing: 0;`. Required because sticky
  `th` is inert in Chromium under `border-collapse: collapse`. Visual
  parity expected: the table styling uses only per-cell `border-bottom`
  (th 2px, td 1px), no shared/collapsed borders. `.data-table` is a global
  class — after the change, eyeball the other `.data-table` sites
  (dashboard tables, detail pages) for border artifacts; none expected.
- `.data-table th` keeps `top: var(--topbar-height); z-index: 40;` — with
  the overflow wrapper gone (below) and `position: sticky` still set inline
  by `resizable_columns.js`, the viewport becomes the scrollport and the
  offset finally means what it was always intended to mean.
- `th` background is already opaque (`var(--bg-secondary)`) — required so
  rows scrolling underneath are hidden; do not make it transparent.

### 2. Templates (4 list pages)

- Remove `style="overflow-x: auto;"` from the table wrapper div (keep the
  div itself). This simultaneously (a) removes the wrong scroll container
  so sticky headers work against the page, (b) removes the horizontal
  scrollbar, and (c) removes the trigger for the Chromium paint bug.

### 3. `static/js/resizable_columns.js`

- **Zero-sum drag:** the handle on `th[i]` resizes the pair
  `(th[i], th[i+1])`: `th[i]` grows by the drag delta, `th[i+1]` shrinks by
  the same amount (and vice versa). Clamp both at `MIN_COL_WIDTH = 40` px —
  the drag stops giving/taking once either side hits the floor. The **last
  column gets no handle** (no right-hand neighbour; it's the Actions column
  on all 4 lists).
- **Scale-to-fit on apply:** `applyStoredColumnWidths()` — after loading
  saved widths, scale them proportionally so their sum equals the
  container's `clientWidth`, clamping each at `MIN_COL_WIDTH`; assign any
  rounding remainder to the last column so the sum is exact. Persist the
  normalized result back to localStorage (self-heals legacy oversized /
  3px-column entries on first load).
- **Window resize:** re-run the scale-to-fit pass on `window` `resize`
  (debounced ~150ms) so a maximized→restored window never reintroduces
  overflow.
- **Invariant:** `table-layout: fixed` + `width: 100%` (already the case)
  + column widths that always sum to the container width ⇒ the table can
  never exceed the card. There is no code path that sets a width sum
  larger than the container.
- Keep `th.style.position = 'sticky'` (it also serves as the positioned
  ancestor for the absolutely-positioned resize handle).
- Preserve the existing public API (`window.makeColumnsResizable`,
  `window.applyStoredColumnWidths`) and the localStorage key format
  (`colwidths:<tableId>`, array of px numbers) — existing saved values
  must load and be healed, not error or reset.

### 4. Tests (`tests/test_resizable_columns.py`)

- Keep the 4 existing wiring tests.
- Add per-list assertions that the rendered list page no longer contains
  the `overflow-x: auto` wrapper around the list table (regression guard
  for the paint bug's trigger). Scope the assertion to the list template's
  own wrapper, not the whole page (other cards may legitimately keep
  overflow wrappers on other pages — on the 4 list templates the table is
  the only such wrapper today, so a simple "not in body" is acceptable if
  verified true at implementation time).
- JS drag behavior itself remains browser-verified (no JS test runner in
  this suite) — live verification below is the gate.

## Acceptance criteria

1. PO list: with the currently-saved oversized widths present in the
   browser, the first row (PO3839 under default sort) is fully visible on
   load. Verified in Tebello's real Chrome, not only a clean profile.
2. Scrolling any of the 4 lists keeps the header row (labels + filter
   inputs) visible, frozen directly below the topbar.
3. No horizontal scrollbar on any of the 4 lists at any window width
   ≥ 1024px, with default and with saved widths.
4. Dragging a column border resizes it and its right neighbour zero-sum;
   neither goes below 40px; the last column has no resize handle; widths
   persist across reload (scaled to fit).
5. Sort-by-click and per-column filters still work on all 4 lists
   (`table_sort_filter.js` untouched and functional).
6. Full pytest suite green. Offline-first grep clean (no new external
   references).
7. No visible border regression on other `.data-table` pages from the
   `border-collapse` change (spot-check dashboard + one detail page).

## Sequencing (single executor, atomic commit)

One executor, working directly on `master` (small, non-schema,
JS/CSS/template-only batch — same convention as Batches 26/31):
CSS → JS → 4 templates → tests → full suite → commit.
Orchestrator then live-verifies in Tebello's real Chrome (the environment
that reproduces the bug) before closing the batch.

## Post-merge fix — headers were still not freezing (2026-07-22)

Orchestrator live-verification (in Tebello's real Chrome, after commit
`76e33cc`) found acceptance criterion #2 was **not** met: horizontal
scroll and the hidden-first-row paint bug were both fixed, but the column
headers still scrolled away instead of freezing.

**Second root cause (missed in the original spec):** removing the
`overflow-x: auto` wrapper was necessary but not sufficient. The list
`<table>` also sits inside `<div class="card">`, and `.card` has
`overflow: hidden` (main.css) to clip content to its rounded corners.
`overflow: hidden` **is itself a scroll container**, so it — not the
viewport — became the sticky `<th>`'s scrollport, pinning the header to
the card (which scrolls with the page) rather than below the topbar.

Empirically confirmed live at `scrollY = 800` (Sales Orders, 41 rows):

| `.card` overflow | header `<th>` viewport-top | frozen? |
|------------------|---------------------------|---------|
| `hidden` (was)   | −649px (scrolled off)     | no      |
| `visible`        | 56px (below 56px topbar)  | yes     |
| `clip`           | 56px (below 56px topbar)  | yes     |

**Fix:** scoped, not global. Added a `card-sticky-head` modifier class to
the 4 list-page cards and a rule `.card.card-sticky-head { overflow: clip; }`.
`clip` still clips to the card's rounded corners (unlike `visible`, which
would let the table's square corners poke out) but is **not** a scroll
container, so the sticky header freezes against the viewport. Scoped to the
4 list cards rather than changing the global `.card` rule, so detail/other
pages' behavior is untouched. The 4 wiring tests each gained a
`card-sticky-head` presence assertion. Verified live afterward: at
`scrollY = 800` the topbar occupies 0–56px and the header row 56–118px,
both frozen and stacked.
