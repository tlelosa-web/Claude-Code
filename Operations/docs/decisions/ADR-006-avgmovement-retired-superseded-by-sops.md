# ADR-006 — `8. AvgMovement` retired, superseded by SOPS

**Date:** 2026-07-17
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

A 2026-07-17 cross-project status pass found `8. AvgMovement` (a standalone
Excel pipeline, DCOE-onboarded under ADR-003) hadn't produced a report or had
its source data refreshed since 2026-05-13 — over two months stale. Reading
its actual logic (`4_Scripts/item_movement_report.py`) surfaced three
capabilities computed from Sage ERP exports that SOPS didn't have: Supplier +
Lead Time per item, and AMU (average monthly usage) with automated Min/Max
reorder-level suggestions.

Tebello's principle going in: "no need for multiple processes that do the
same or similar things." Retirement was first proposed the same day but held
off — AMU/Min-Max had no SOPS equivalent yet, and retiring the pipeline at
that point would have dropped real capability, not just deduplicated it.

Both gaps have since been closed, built directly into SOPS on the same day:

- **SOPS Batch 32** (`2. SOPS/docs/specs/supplier-lead-time-import-2026-07-
  17.md`, commit `fe06eaa`) — Supplier + Lead Time, imported from Sage's
  `OutstandingPOByItemReport.csv`. On Order was deliberately *not* duplicated
  from this source — SOPS already computed `qty_on_order` live from its own
  Purchase Orders, and importing a second on-order figure would have
  recreated the exact problem this work exists to avoid.
- **SOPS Batch 33** (`2. SOPS/docs/specs/amu-minmax-reorder-suggestion-2026-
  07-17.md`, commit `112e321`) — AMU + suggested Min/Max, imported from
  Sage's `ItemMovementReport.csv`, reusing Batch 32's already-imported lead
  time rather than recomputing it a second way. Kept as new, separate fields
  (`amu`/`suggested_min`/`suggested_max`) — never written into SOPS's
  existing, manually-curated `reorder_point`/`max_level`/`reorder_qty`
  (Batch 25), so nothing Tebello already set by hand was overwritten.

With both landed, every calculation AvgMovement performs has a SOPS
equivalent, live inside the system Tebello actually works in day to day,
rather than a separate manually-run Excel pipeline reading a periodically
hand-refreshed CSV snapshot.

## Decision

1. **`8. AvgMovement` is retired.** It is no longer the source of truth for
   Supplier, Lead Time, AMU, or Min/Max reorder suggestions — SOPS is, once
   Tebello runs the two pending migrations + real-data imports flagged in
   `2. SOPS/docs/todo.md` Batches 32/33 (not yet run against `instance/sops.db`,
   same standing convention as every other schema change in that repo).
2. **Nothing in the `8. AvgMovement` folder is deleted or moved as part of
   this ADR.** `RUN_PIPELINE.bat`, `4_Scripts/`, `3_Live_Reports/*.xlsx`
   (production data per that project's own `CLAUDE.md`), and
   `2_Source_Data/` are all left exactly as they are. This ADR is a status
   change, not a cleanup — deleting/archiving the folder's contents is a
   separate, explicit decision for Tebello to make later if wanted (hub
   `CLAUDE.md` hard rule 4: ask before touching production data paths).
3. **`8. AvgMovement/CLAUDE.md` gets a retirement notice** at the top,
   pointing to this ADR and to SOPS Batches 32/33, so a future session
   opening that folder cold knows immediately it's superseded rather than
   treating it as a live pipeline to fix or run.
4. **Root `CLAUDE.md` project index**: status column updated from
   "✅ Lightweight DCOE" to "🔴 Retired — superseded by SOPS Batches 32/33
   (ADR-006)".
5. **`docs/patterns.md` § 6** (pipeline folder layout) is unaffected — it's a
   historical record of where the convention was observed, not a live
   pointer to AvgMovement's status.

## Consequences

- Tebello should stop running `RUN_PIPELINE.bat` going forward — Supplier/
  Lead Time/AMU/Min-Max now live in SOPS's Stock Report and Item detail
  pages instead, refreshed via SOPS's own CSV import flow.
- The two source CSVs AvgMovement reads (`ItemListingReport.csv`,
  `ItemMovementReport.csv`) and the one it doesn't share with SOPS
  (`OutstandingPOByItemReport.csv`) still need to be exported from Sage and
  uploaded into SOPS periodically via its three import buttons — this ADR
  doesn't change *how often* the underlying Sage data needs refreshing, only
  *where* it gets imported to.
- If a genuine gap is later found (AvgMovement did something SOPS's Batch
  32/33 port didn't faithfully replicate), that's a bug report against the
  SOPS batches, not a reason to un-retire AvgMovement.
- Deleting the `8. AvgMovement` folder's contents, or archiving it out of
  the `Operations` tree entirely, is explicitly **not** decided here —
  revisit only if/when Tebello asks for that separately.
