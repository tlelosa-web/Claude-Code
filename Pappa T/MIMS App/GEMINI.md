# PROJECT: MIMS ERP v2

# VERSION: 2.0.0

## 1. DIRECTIVE (The Brain)

**Role:** Lead Product Manager & Systems Architect.
**Objective:** Build a production-ready, full-stack MRP (Manufacturing Resource Planning) application with high-fidelity UI and deep traceability.
**Success Criteria:**

* **Type-Safety:** Full TypeScript integration between Supabase schema and Next.js frontend.
* **Data Integrity:** Multi-level BOMs and Batch tracking must maintain 100% mathematical parity.
* **Resilience:** The system must self-heal from null database responses or expired sessions via the Annealing Gate.

## 2. ENVIRONMENT & TOOL AUDIT

**Stack Constraints:** Next.js 14 (App Router), Tailwind CSS, Supabase (PostgreSQL + Auth + RLS).
**Required Tools:**

* **Framework:** Next.js v14+
* **Database/Auth:** Supabase CLI / Client SDK
* **Styling:** Tailwind CSS + Headless UI/Radix
* **Package Manager:** npm

**Pre-Flight Protocol:** Verify `.env.local` for Supabase credentials. Ensure `npm install` has been executed before attempting Server Action triggers.

## 3. ORCHESTRATION (The Architect)

**Workflow Sequence:**

1. **Discovery:** Audit existing 10-table schema and 9 RPC functions for Stage 3 compatibility.
2. **Analysis:** Identify data gaps in "Shop Floor" requirements (e.g., real-time time tracking vs. static task logs).
3. **Drafting:** Outline the Tablet-optimized UX and Advanced Traceability logic.
4. **Validation:** Pass logic through Section 5 (Self-Annealing) to ensure Auth and RLS don't block operator roles.
5. **Finalization:** Deploy Server Actions and update UI components.

## 4. EXECUTION (The Worker)

* [x] **Task 1:** Initialize repository, auth, layout shell, and SQL migrations.
* [x] **Task 2:** [MRP Stage 1] Schema Overhaul (Unified Items, Multi-Level BOMs, Batches).
* [x] **Task 3:** [MRP Stage 2] Backend Logic V2 & UI Refactor (Inventory, Products, Costing).
* [ ] **Task 4:** [MRP Stage 3] Build tablet Workcell Operator Dashboard using App Router + Supabase Realtime for live work orders. Annealing Check: Logic Breach: operators see unassigned orders; Validation: enforce RLS where workcell_id = operator.workcell_id and refresh session on 401 before fail.
* [ ] **Task 5:** [MRP Stage 3] Implement time tracking server actions and schema (start/pause/resume/stop) with non-overlapping operator sessions. Annealing Check: Logic Breach: overlapping active sessions; Validation: partial unique index on (operator_id, operation_id) where active = true and auto-close any active session before opening a new one.
* [ ] **Task 6:** [MRP Stage 3] Add barcode/QR scanning to resolve items, batches, and serials in operator flows. Annealing Check: Logic Breach: mislinked scan to wrong item; Validation: verify scanned token's item_id matches operation BOM requirement; reject if mismatch and re-prompt.
* [ ] **Task 7:** [MRP Stage 3] Implement component consumption with atomic stock moves, backflush support, and scrap booking. Annealing Check: Logic Breach: negative on-hand; Validation: transactionally assert available_qty - consume_qty >= 0, else abort; on PostgrestError 23505 retry once with generated unique pointer.
* [ ] **Task 8:** [MRP Stage 3] Add operation completion flow to post finished quantities and issue finished-good batches/serials by item tracking policy. Annealing Check: Logic Breach: orphan serials without parent batch; Validation: require finished batch FK exists before serial creation; on 23503 create missing batch and retry once.
* [ ] **Task 9:** [MRP Stage 3] Capture defects and downtime with cause codes tied to time sessions and operations. Annealing Check: Logic Breach: unclosed events inflate cycle time; Validation: auto-close open defect/downtime records on session stop; assert sum(state_durations) = session_elapsed.
* [ ] **Task 10:** [Traceability] Implement batch-to-serial linkage and component genealogy API/view for forward/backward trace. Annealing Check: Logic Breach: missing genealogy rows; Validation: on completion, upsert genealogy for each consumed component; block completion if any component-to-serial link is absent.
* [ ] **Task 11:** [Auth/RLS] Define operator-role RLS and RPCs (consume_materials, complete_operation, create_serials) to constrain writes. Annealing Check: Logic Breach: privilege escalation via direct table writes; Validation: allow writes only where operator_id = auth.uid() via SECURITY DEFINER RPCs with explicit guards; on 401, trigger session refresh before error.
* [ ] **Task 12:** [Annealing Gate] Wrap Shop Floor server actions with self-healing (401 refresh, PostgrestError handling, data re-checks). Annealing Check: Logic Breach: null/expired session breaks operator flow; Validation: on 401 attempt session refresh once; on $0 BOM cost, re-run sub-assembly aggregation; re-verify item_id in unified_items before inventory updates.
* [ ] **Task 13:** [Stage-3 E2E] Add end-to-end tests for "start job -> scan -> consume -> pause/resume -> complete -> genealogy check". Annealing Check: Logic Breach: tests bypass RLS; Validation: run tests against operator role with RLS enabled; assert policy enforcement on all critical writes.

## 5. SELF-ANNEALING GATE (The Heal)

**Validation Rules:**

* **Auth Self-Healing:** If a Server Action fails with a 401, trigger a session refresh check before throwing a terminal error.
* **Data Integrity (MRP):** Before updating inventory levels, the agent must verify the `item_id` exists in the `unified_items` table. If missing, search the `products` table for a reference error.
* **Logic Check:** If a BOM cost calculation results in `$0.00`, re-run the aggregation across all sub-assemblies to find the missing cost-input.
* **Error Recovery:** On Supabase "PostgrestError", log the specific code (e.g., 23505 for uniqueness), attempt to generate a unique suffix or pointer, and retry the insert once.

## 6. PROJECT STATE & LOG

* **Last Update:** 2026-03-11
* **Current Status:** In-Progress (Transitioning to Stage 3: Shop Floor)
* **Blockers:** None.
