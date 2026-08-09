# delivery-note-system

Next.js 16 (App Router) + TypeScript + Prisma ORM + SQLite delivery-note
register for Fan Movement (Pty) Ltd. Own git repo
(`Desktop/Operations/7. DELIVERY NOTE/delivery-note-system`, no remote
configured), onboarded to DCOE 2026-07-15. Single-operator tool, no auth.
Path corrected 2026-08-09 — the `C:\Dev\Operations\…` path this line carried
recorded a real relocation off the OneDrive-synced Desktop, but that was
while Operations was its own machine; `C:\Dev` does not exist since the
2026-08-03 consolidation.

## 2026-07-28 — Stack facts and gotchas
**Source:** delivery-note-system `CLAUDE.md` / `docs/todo.md` / `docs/bugs/`
**Status:** active

- **Stack:** Next.js 16.2.6 (postdates most AI training data — real breaking
  changes exist, check `node_modules/next/dist/docs/` before assuming
  training-data knowledge of routing/config/API-route conventions still
  applies) + Prisma ORM + SQLite (`dev.db`, gitignored) + shadcn/ui + sonner.
- **Prisma 7.8.0 driver-adapter requirement:** `schema.prisma` must declare a
  datasource `url` and use a driver adapter (`@prisma/adapter-better-sqlite3`
  here) — Prisma 7's architecture no longer tolerates a missing datasource
  URL the way older versions silently did. Omitting it makes every DB-backed
  route 500, not just new ones. This was a latent pre-existing gap that only
  surfaced when the Prisma Client was regenerated for an unrelated schema
  change — worth checking proactively on any Prisma 7 project.
- **Turbopack + Windows junction points:** Turbopack can fail linking a
  regenerated Prisma client into `.next/dev/` with a Windows junction-point
  error. Workaround: `next dev --webpack` instead of the Turbopack default.
  Possibly machine-specific — not applied as the project default.
- **`src/lib/prisma.ts` singleton pattern:** uses the standard Next.js
  dev-mode `globalThis.prismaGlobal` singleton to avoid exhausting DB
  connections on hot reload — always import the client from here, never
  `new PrismaClient()` directly elsewhere.
- **DN-number generation gotcha (fixed 2026-07-17/18):** originally derived
  the next delivery-note number from the *most recently created* record,
  which would have broken (collide or skip) if a record were ever deleted or
  backdated. Fixed to derive from the numeric max instead, which is what
  made Delete safe to ship. Worth checking for the same "most-recent-row"
  assumption in any similar auto-incrementing-ID-from-data pattern elsewhere.
- **Schema-as-contract convention:** `prisma/schema.prisma` changes must
  update the API routes and the frontend's TypeScript interface/form
  together in the same task — never one layer in isolation.

## 2026-07-28 — Outstanding items
**Source:** delivery-note-system `docs/todo.md`
**Status:** active

- No automated test suite yet (no `tests/` folder, no test runner
  configured) — not urgent for current MVP scope, flagged to add before the
  feature grows (e.g. if auth is added).
- `README.md` is still default `create-next-app` boilerplate, not
  delivery-note-specific — low priority, update opportunistically.
- Open question (not urgent): whether `dev.db` should ever be
  seeded/reset as part of a documented workflow, or stays purely local
  scratch state.
