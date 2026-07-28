## 2026-07-28 — What it is, stack, current stage
**Source:** Pappa T session (cross-project status survey), MIMS App's own GEMINI.md, package.json
**Status:** active

MIMS ERP v2 — a Manufacturing Resource Planning (MRP) web app. Next.js 14 (App
Router), TypeScript, Tailwind CSS, Supabase (PostgreSQL + Auth + RLS). Lives at
`Pappa T/MIMS App/` — folder inside the Pappa T vault repo, not its own git repo.

**Notable:** this project's brain file is `GEMINI.md`, not `CLAUDE.md` — it was
built/is being driven with Gemini rather than Claude Code as the primary agent,
unlike every other sub-project in this vault. Its own directive frames itself with
a "Directive → Orchestration → Execution / Self-Annealing Gate" structure (not
DCOE) — e.g. a described self-healing pattern for Server Actions: on a 401, retry
a session refresh before throwing; on a `$0.00` BOM cost, re-run sub-assembly cost
aggregation before treating it as a real zero; on Supabase `PostgrestError` 23505
(uniqueness violation), retry once with a generated unique suffix.

**Status as of last update (2026-03-11):** in progress, transitioning into
"Stage 3: Shop Floor" — Tasks 1-3 (repo/auth/schema, MRP schema overhaul, backend
v2 + UI refactor for inventory/products/costing) done; Tasks 4-13 (tablet Workcell
Operator Dashboard via Supabase Realtime, time-tracking with non-overlapping
sessions, barcode/QR scanning, component consumption with atomic stock moves,
finished-goods batch/serial issuance, defect/downtime capture, batch-to-serial
genealogy trace, operator-role RLS + RPCs, end-to-end Shop Floor tests) not yet
started. Blockers: none noted.

**Reusable facts:**
- Auth/RLS-heavy design: writes are meant to go through `SECURITY DEFINER` RPCs
  (`consume_materials`, `complete_operation`, `create_serials`) rather than direct
  table writes, to prevent privilege escalation via the client.
- Data-integrity pattern: before any inventory update, verify `item_id` exists in
  a `unified_items` table (search `products` for a reference error if missing) —
  a "verify the FK target actually resolved" convention, not just a foreign-key
  constraint.
- Stack detail: `@supabase/ssr` + `@supabase/supabase-js`, Next 14.2.18, React 18,
  Tailwind 3.4, TypeScript 5. `COMPLETE_SUPABASE_MIGRATION.sql` at the project root
  suggests migrations aren't (yet) split into Supabase's usual per-migration file
  convention — worth confirming before assuming a `supabase/migrations/*.sql`-per-
  change discipline is already in place (a `supabase/migrations/` folder does exist
  alongside it, so this may already be transitioning).

**Not carried over:** no business/inventory data, no specific schema/table
contents — this entry is stack + architecture-pattern only, per the no-company-
data rule.
