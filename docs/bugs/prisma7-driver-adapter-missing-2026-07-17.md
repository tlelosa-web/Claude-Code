# Bug — Every Prisma-backed route 500'd after regenerating the client (Prisma 7 driver adapter requirement)

**Found:** 2026-07-17/18, while verifying the edit/delete/PDF-export batch
(`docs/specs/edit-delete-pdf-export-2026-07-17.md`) in the browser.
**Status:** Fixed, same session.

## Symptom

`GET /api/dn` and `GET /api/dn/next` (and by extension every other Prisma
query in the app) returned 500. This wasn't limited to the new Edit/Delete/
PDF code — the pre-existing list/register endpoints broke too.

## Root cause

`prisma/schema.prisma`'s `datasource db` block never had a `url` field —
apparently harmless under whatever Prisma client was generated at the
original MVP scaffold. Adding `updatedAt` to the schema (Step 1 of the
edit/delete/PDF batch) required running `npx prisma migrate dev`, which
regenerated the Prisma Client under the currently-installed **Prisma 7.8.0**.

Prisma 7 removed the classic bundled query-engine-binary approach in favor
of **driver adapters** — `new PrismaClient()` with no adapter now throws
`PrismaClientInitializationError`. Adding `url = env("DATABASE_URL")` back
into `schema.prisma` doesn't work either — Prisma 7 explicitly rejects it at
schema-validation time (`P1012`: "The datasource property `url` is no
longer supported in schema files... pass `adapter` ... to the `PrismaClient`
constructor").

## Fix

- Added `@prisma/adapter-better-sqlite3` (Prisma's official adapter for a
  local file-based SQLite database — matches this project's `provider =
  "sqlite"` and local `dev.db` file, no other adapter fits this use case).
- `src/lib/prisma.ts`: constructs `new PrismaBetterSqlite3({ url:
  process.env.DATABASE_URL })` and passes it as `new PrismaClient({ adapter
  })`. The adapter strips a leading `file:` prefix internally, so the
  existing `.env`'s `DATABASE_URL="file:./dev.db"` needed no change.
- Ran `npx prisma generate` to regenerate the client against the new
  adapter-based config.

## Why this matters going forward

This wasn't introduced by this batch — it was a **latent, pre-existing gap**
that only surfaced because a schema change forced a client regeneration
under the now-installed Prisma 7. Any future schema change that triggers
`prisma migrate dev`/`prisma generate` would have hit this the same way.
Now that the adapter is wired in, this class of failure shouldn't recur.

## Related, separate issue also hit during verification (not a code bug)

Turbopack (this project's default dev bundler under Next.js 16.2.6) failed
with `failed to create junction point ... Access is denied (os error 5)`
when trying to link the regenerated `@prisma/client` into
`.next/dev/node_modules/@prisma/`, on this Windows machine. Deleting `.next`
did not resolve it. Running the dev server with `next dev --webpack`
(Next's documented Turbopack opt-out) sidestepped it entirely — this project
still defaults to Turbopack (`npm run dev` is unchanged), since this may be
specific to this machine/environment rather than a universal Windows issue.
If it recurs, `npm run dev -- --webpack` (or editing the `dev` script) is
the known workaround; worth a permanent switch only if it keeps happening.
