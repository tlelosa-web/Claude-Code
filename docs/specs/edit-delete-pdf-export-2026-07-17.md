# Spec — Edit / Delete / PDF Export for Delivery Notes

**Date:** 2026-07-17 | **Status:** Pending approval | **Owner:** Tebello Lelosa

## Scope (confirmed with Tebello via AskUserQuestion)

- **One combined spec, sequenced build.** Edit, Delete, and PDF export all
  touch the same register table/row, so they're planned together — but
  built in the order below so each step is independently working and
  committable.
- **DN-number generation bug fixed as part of this work**, not left latent.
  Today `GET /api/dn/next` (`src/app/api/dn/next/route.ts`) takes the
  *most-recently-created* row and increments its numeric suffix. Once
  Delete exists, deleting the newest row and creating another would
  reissue (or skip) a number. Fixed to compute off the numeric max across
  all existing `dnNumber`s instead.
- **PDF export = one real PDF file per note, on-demand** (a "Download PDF"
  action per register row), not a browser print-CSS view — mirrors the
  "downloadable document" expectation, distinct from SOPS's print-to-A4
  pattern (SOPS documents are printed HTML, not generated PDF files).
- **Edit fields: Date, Customer, Description.** `dnNumber` stays locked
  once issued — it's the permanent identifier the whole app is built
  around (see `CLAUDE.md` § Architecture Notes). No extra confirmation
  step on save (no auth/audit trail exists yet regardless, so a confirm
  dialog wouldn't add real protection).

## Current state (for context, no change needed to re-verify)

- `prisma/schema.prisma` — single `DeliveryNote` model: `id`, `dnNumber`
  (unique), `date`, `customer`, `description`, `createdAt`. No `updatedAt`.
- `src/app/api/dn/route.ts` — `GET`, lists all notes newest-first.
- `src/app/api/dn/register/route.ts` — `POST`, creates a note (dupe
  `dnNumber` check, all 4 fields required).
- `src/app/api/dn/next/route.ts` — `GET`, computes the next `dnNumber` (the
  bug being fixed in Step 0).
- `src/app/page.tsx` — single client component: register form (left) +
  history table (right, DN#/Date/Customer/Description columns only, no
  Actions column yet).
- `src/components/ui/` — has `button`, `input`, `table`, `label`, `card`,
  `sonner`. **No `dialog` or `alert-dialog` component yet** — needed for
  the edit modal and delete confirmation.
- No PDF-generation dependency in `package.json` today.

## Step 0 — DN-number generation fix

**File:** `src/app/api/dn/next/route.ts`

Replace the `findFirst({ orderBy: { createdAt: 'desc' } })` lookup with a
`findMany({ select: { dnNumber: true } })` over all notes. Parse every
`dnNumber` with the existing `/^(.*?)(\d+)$/` regex, track the highest
parsed `{ prefix, number, padLength }` numerically (not lexicographically,
and not by row recency). Rows that don't match the pattern are skipped
(don't crash, don't count toward the max) — mirrors today's single-row
fallback behavior, just applied across the whole set. Empty table still
returns `"FM-DN0001"`. If no row matches the pattern at all (theoretical,
pre-existing edge case), fall back to today's `currentDn + "-1"` behavior
using the most-recently-created row's raw string.

## Step 1 — Edit

**Files:**
- `src/app/api/dn/[id]/route.ts` (new) — `PATCH` handler. Accepts
  `{ date, customer, description }`; 400 if any is missing/blank. Looks up
  by `id`, 404 if not found. Updates only those 3 fields — `dnNumber` is
  never read from the request body, even if present, so it can't be
  overwritten via a crafted payload. Add `updatedAt DateTime @updatedAt` to
  the `DeliveryNote` model (`prisma/schema.prisma`) + `npx prisma migrate
  dev` to generate the migration — cheap, standard Prisma pattern, useful
  once edits exist even though nothing surfaces it in the UI yet.
- `npx shadcn@latest add dialog` — scaffolds `src/components/ui/dialog.tsx`
  in this project's existing shadcn style, rather than hand-rolling a modal
  primitive from scratch.
- `src/app/page.tsx` — register table gains an **Actions** column. Edit
  button opens a `Dialog` pre-filled with the row's Date/Customer/
  Description (DN Number shown read-only inside the dialog, matching the
  form's existing disabled-input pattern for the auto field). Save → `PATCH
  /api/dn/[id]` → on success, close dialog, toast, refetch `fetchDns()`.

## Step 2 — Delete

**Files:**
- `src/app/api/dn/[id]/route.ts` — add `DELETE` handler. Looks up by `id`,
  404 if not found, otherwise `prisma.deliveryNote.delete()`. Hard delete
  (no soft-delete/archive flag) — matches this app's current no-auth,
  single-operator, no-audit-trail design; nothing else in the schema
  assumes soft-delete.
- `npx shadcn@latest add alert-dialog` — for a real confirm-before-delete
  step (distinct from the edit `Dialog`, matches shadcn's own
  destructive-action convention).
- `src/app/page.tsx` — Delete button in the Actions column opens an
  `AlertDialog` ("Delete DN-0054? This can't be undone."). Confirm → `DELETE
  /api/dn/[id]` → toast, refetch **both** `fetchDns()` and `fetchNextDn()`
  (deleting the highest-numbered row changes what Step 0's fix computes as
  next).

## Step 3 — PDF export

**Files:**
- `package.json` — add `pdf-lib` (pure JS/TS, no native binary, works
  directly in a Next.js Node-runtime API route — no browser/headless-
  Chrome dependency like `puppeteer` would need).
- `src/app/api/dn/[id]/pdf/route.ts` (new) — `GET` handler,
  `export const runtime = "nodejs"`. Looks up the note by `id`, 404 if not
  found. Builds a single A4 page with `pdf-lib`: "Fan Movement (Pty) Ltd —
  Delivery Note" header, then DN Number / Date / Customer / Description as
  labeled fields, then a "Received by: ______  Date: ______" signature
  line. Text-only layout (no logo image — nothing to source one from right
  now; easy to add later as a follow-up if wanted). Returns the PDF bytes
  with `Content-Type: application/pdf` and `Content-Disposition:
  attachment; filename="<dnNumber>.pdf"`.
- `src/app/page.tsx` — "Download PDF" action in the Actions column, plain
  `<a href="/api/dn/{id}/pdf">` (or `window.location`) — a real file
  download, no client-side PDF library needed since generation is
  server-side.

## Testing / verification plan

No automated test suite exists in this project yet (`CLAUDE.md` § Testing
Standards — tracked separately in `docs/todo.md`, not part of this spec's
scope). Manual verification before considering each step done:

- **Step 0:** seed 3+ notes out of creation order (e.g. via `prisma
  studio`, create `FM-DN0010` after `FM-DN0009` then edit timestamps, or
  simpler — register notes, delete the newest, register again) and confirm
  `/api/dn/next` always returns `max(existing) + 1`, never a collision.
- **Step 1:** edit a note's Date/Customer/Description, confirm the table
  reflects the change and `dnNumber` is unchanged; attempt a PATCH with
  `dnNumber` in the body (e.g. via curl) and confirm it's ignored.
- **Step 2:** delete a note, confirm it disappears from the table and the
  next-DN preview on the form updates correctly; confirm the `AlertDialog`
  blocks accidental single-click deletes.
- **Step 3:** click Download PDF on a real note, confirm the file opens
  and shows correct DN Number/Date/Customer/Description; confirm the
  filename matches the DN number.
- Re-run `npm run lint` clean on all touched/new files before considering
  the batch done (no test runner to gate on, per this project's current
  state).

## Acceptance criteria

- [ ] `/api/dn/next` computes off numeric max, not most-recent-created.
- [ ] Edit updates Date/Customer/Description only; `dnNumber` immutable
      even against a crafted request body.
- [ ] Delete removes the row, requires confirmation, and the next-DN
      preview updates correctly afterward.
- [ ] PDF download produces a correctly-populated, correctly-named file
      for any given note.
- [ ] `npm run lint` clean on all touched/new files.
- [ ] `dev.db` not touched/committed as a side effect (per this project's
      hard rule 3).
