## Task: Native Sales Order Report Excel export (replicate `1. Daily Sales Order Files` pipeline inside SOPS)

**Domain:** Software / AI
**Date:** 2026-07-17 (revised twice same day — see Revision notes)
**Requested by:** Tebello Lelosa
**Batch:** 34 (originally requested as "Batch 33" — corrected during spec-writing: `docs/todo.md` already had a Batch 33, "AMU + suggested Min/Max reorder levels from Sage," shipped and committed `112e321` before this spec was written.)
**Status:** Ready for dispatch — all design questions from both questionnaire rounds are now resolved. No open questions remain.

**Revision note 1 (2026-07-17):** Tebello ran a proper questionnaire on
the status design after the original Decision 1 ("separate manual
`report_status` dropdown") and Decision 2 ("single current-state tab, no
history") were flagged as needing confirmation. The answers materially
change both: `report_status` is now a **computed property**, not a stored
manual field, driven by real WO/STO events plus one manual On Hold flag; and
a full change-history log is now **in scope** (was previously deferred).

**Revision note 2 (2026-07-17, final pass before dispatch):** Tebello
answered the four open questions left after revision 1: (1) `Ready-Dispatch`
now means **all** linked WOs/STOs complete, not "any" — property logic
updated below; (2) WO `In Progress` confirmed to stay unwired, no change;
(3) STO Edit-from-`Released` confirmed allowed — the template-ripple bullet
is no longer a recommendation, it's a requirement; (4) the "2-job Total
correction" was **not** a Sage data bug — it was partial-payment netting,
already solved by the existing `SalesOrder.balance_due` property (Batch 24).
This resolved into dropping `total_override`/`display_total` entirely (see
Decision 3, substantially rewritten) — the export's `Total` column now
sources `balance_due` directly, and the pre-existing `amount_paid`
reset-on-overwrite gap is pulled into this batch's `save_order()`
carry-forward fix rather than deferred, since it now directly affects this
batch's own export accuracy. The default `?view=open` export population is
confirmed, not just recommended. All sections below reflect this final
state — schema/migration plan, sequencing, tests, and acceptance criteria
were all adjusted accordingly.

---

### Goal

Give SOPS an on-demand Excel export ("Sales Order Report") generated live from
its own `SalesOrder`/`SOLineItem`/`WorksOrder` data, functionally replacing
the standalone `1. Daily Sales Order Files` pipeline's daily-regenerated
report — without depending on Sage CSV exports for Sales Order data or on the
colleague-owned OneDrive Contract Register / Released Jobs PDF folders. Runs
**alongside** the standalone pipeline during a transition period; that
pipeline is not touched or decommissioned by this batch.

---

### Confirmed by Tebello — do not re-litigate

1. Output is an on-demand Excel export generated from SOPS's own DB.
2. Standalone pipeline keeps running in parallel during transition — not decommissioned here.
3. Same population as today: every Sage FM job number in the report already gets an SO PDF into SOPS, so this reuses `SalesOrder`/`SOLineItem` — no separate Sage-CSV-driven entity for jobs themselves.
4. No OneDrive/Contract-Register/Released-Jobs dependency — SOPS already solves SO↔FM-number matching via `SOLineItem.job_number` / `SalesOrder.job_numbers`.
5. Monthly INV tab is in scope. Needs a new importer for `CustomerInvoicesReport.csv`, following `services/item_importer.py` / `services/po_by_item_importer.py` conventions (incl. `_safe_copy_for_reading()`).
6. **Status design — locked in, see Decision 1 below.** All three order types get a status that is fully computed from real events, no dropdown, except a single manual On Hold flag on the Sales Order. `Ready-Dispatch` means every linked WO/STO is complete (not "any").
7. **History — locked in, see Decision 2 below.** An event-driven change log is a real deliverable, scoped to a fixed field list, surfaced as one filterable Change Log report — not a per-order timeline, not a point-in-time Excel export.
8. **Total/override design — locked in, see Decision 3 below.** The export's `Total` column uses the existing `SalesOrder.balance_due` property (already `total_incl - amount_paid`); no separate `total_override` field is built. `report_notes`, `on_hold`/`on_hold_reason`, and (newly, per this revision) `amount_paid` all get `save_order()` overwrite-carry-forward protection.
9. Default export population: `?view=open` (Draft+Open SOs), matching Batch 16/21's list-page convention — confirmed, not just recommended.

---

### Source system reviewed

`1. Daily Sales Order Files/4_Scripts/update_sales_report.py` (main daily-tab
builder), `update_invoice_tab.py` (Monthly INV tab), `update_payment_status_col_j.py`,
`apply_report_changes.py`, `2_Source_Data/CustomerInvoicesReport.csv` (real
header row + sample rows).

Findings (corrected per revision 2 where noted):

- The old report's Payment Status column is already a subset of SOPS's
  existing `PAYMENT_STATUS_OPTIONS` — no new field needed, reuse
  `SalesOrder.payment_status` as-is.
- **Corrected finding (was originally mis-attributed to a Sage data bug):**
  the old report's Total (column G) is never carried forward between daily
  rebuilds, and 2 specific jobs (FM4047/FM4164) needed a manual Total
  correction reapplied every day. Per Tebello's clarification in revision
  2, this was **not** a Sage source-data bug — those 2 jobs were partially
  paid, and the manual edit was subtracting the amount already paid from
  the gross total (i.e. showing balance owing, not the full order value).
  SOPS already solves this generically via `SalesOrder.balance_due`
  (`total_incl - amount_paid`, added Batch 24) — see Decision 3.
- The old report's Details (column K) is carried forward, but only as an
  opaque last-value copy with no system/manual distinction.
- Nothing in the pipeline scripts encodes "ON HOLD" as logic — it was a
  pure manual Excel edit.

---

## Decision 1 (locked in, final) — Status is computed from events, not a dropdown, except one manual On Hold flag

All three order types (`SalesOrder`, `WorksOrder`, `StockOrder`) get a
status that is fully derived from real SOPS actions, with **no user-facing
dropdown anywhere in this design** — the only manual input in the whole
status system is a single On Hold flag on the Sales Order.

Every derivation below was verified against the actual route code
(`routes/sales_orders.py`, `routes/works_orders.py`, `routes/stock_orders.py`)
before finalizing, per Tebello's explicit instruction not to assume from the
workflow description alone. Findings are called out inline.

#### Sales Order — `SalesOrder.report_status`, a **computed property**, not a stored column

```python
@property
def report_status(self):
    if self.status in ('Closed', 'Cancelled'):
        return None  # not shown/relevant — SalesOrder.status already covers closure
    orders = list(self.works_orders) + list(self.stock_orders)
    if not orders:
        return 'Loaded'
    all_terminal = all(o.status in ('Complete', 'Cancelled') for o in orders)
    any_complete = any(o.status == 'Complete' for o in orders)
    if all_terminal and any_complete:
        return 'Ready-Dispatch'
    return 'Released'

@property
def display_report_status(self):
    base = self.report_status
    if base is None:
        return None
    return f"{base} — On Hold" if self.on_hold else base
```

- **`Loaded`** — SO uploaded/saved, no Works Pack built yet (`not orders`).
- **`Released`** — a WO or STO has been generated from this SO, and the
  job isn't fully complete yet.
- **`Ready-Dispatch`** — **every** linked WO and STO is in a terminal state
  (`Complete` or `Cancelled`) **and at least one is actually `Complete`**
  (not all-`Cancelled`). This is the *all*-based rule confirmed in revision
  2, replacing the original *any*-based draft.
- SO `Closed`/`Cancelled` → `report_status` returns `None` (not shown).
  Extended from Tebello's original "no terminal value needed once
  `SalesOrder.status == 'Closed'`" to also cover `Cancelled`, the other
  terminal `SalesOrder.status` value that exists in the code
  (`routes/sales_orders.py` `cancel_order()`) — a small, low-risk extension.
- **Edge case, deliberately handled, not just an afterthought:** an SO
  whose WOs/STOs are *all* `Cancelled` (no completions at all) reads as
  `Released`, not `Ready-Dispatch` — the `any_complete` guard exists
  specifically to avoid the vacuous-truth bug Tebello flagged (an
  all-`Cancelled` set trivially satisfies "every order is terminal" without
  meaning anything is actually done). There's no dedicated "abandoned/all
  cancelled" label in the 3-value vocabulary — it falls through to
  `Released` as the general "still not ready" bucket, which is accurate
  enough (nothing is dispatchable) without inventing a 4th value nobody
  asked for.

**Verification finding — "Processing" dropped, not just deferred:** Tebello
asked whether there's an observable gap between "Build BOM started" and
"WO/STO generated," or whether SOPS creates them atomically. Confirmed by
reading `build_bom()` (`routes/sales_orders.py` lines 191–417): the `GET`
request only renders the form (no persistence); the `POST` request creates
the `WorksOrder`(s) and/or `StockOrder` **and** sets `so.status = 'Open'`
all within the same request/transaction (lines 310–314, 380–383, 417).
There is no persisted intermediate state between "form submitted" and
"WO/STO exist" — **`Processing` never becomes observable in the current
code and is dropped from the vocabulary**, not carried as an unused value.
If Tebello later wants a real "build in progress" signal, that requires a
new explicit action (e.g., a save-draft step before the final Build Works
Pack submit) — a separate future feature, out of scope here.

**Resolved (revision 2) — `Ready-Dispatch` is now *all*-based, accepted
consequence:** Tebello confirmed the *all*-complete reading (not "any").
Verified against `can_close_sales_order()` (`routes/sales_orders.py` line
485) — the function driving `SalesOrder.status → 'Closed'` already requires
**all** WOs/STOs to be `Complete`/`Cancelled`, i.e. `report_status`'s
`Ready-Dispatch` condition and the SO's own auto-close condition are now the
*same* predicate. Accepted consequence, per Tebello: for the common
single-WO-or-single-STO SO, `Ready-Dispatch` and `Closed` (report_status →
`None`) resolve in the same commit (`mark_complete()`/`complete_order()`
both call `can_close_sales_order()` immediately after flipping the order's
own status) — so `Ready-Dispatch` is effectively unobservable outside that
one transaction for simple SOs. **This is intentional and not being
solved** — Tebello's own words: "that's fine, don't try to solve it." For
multi-fan SOs, `Ready-Dispatch` now correctly means "the whole job is
ready," not "at least one piece is ready," matching the dispatch-readiness
intent.

#### On Hold — new, separate manual boolean, Sales Order only

```python
on_hold = db.Column(db.Boolean, default=False)
on_hold_reason = db.Column(db.Text)
```

Manually toggled via a dedicated route (`POST /sales-orders/<id>/on-hold`),
displayed as an overlay on the computed `report_status`
(`display_report_status` above), e.g. `"Released — On Hold"`. Explicitly
**not** added to `WorksOrder` or `StockOrder` — SO-level only, per
Tebello's confirmation (given twice, after initially wavering).

#### Works Order — `WorksOrder.status` stays a stored column, gains a value, stays event-driven

New vocabulary: `Open → Released → In Progress → Complete → Cancelled`.

**No schema change required for this** — verified `WorksOrder.status` is a
plain `db.Column(db.String(50), default='Open')` with no `CHECK` constraint,
only a descriptive comment listing valid values. Adding a new string value
is a code-level change (route logic + the comment + `WO_ACTIVE` filter
tuple + template conditionals below), not a migration.

- **`Released` (new)** — fires when the WO is printed. **Verification
  finding:** `works_orders.py print_order()` (`GET /works-orders/<id>/print`)
  is currently a pure render with no persistence at all. Making it status-
  mutating is a genuinely new side effect on a `GET` route — flagged as a
  design note (a `GET` normally shouldn't mutate state), but implemented per
  Tebello's explicit instruction. Guarded to fire **once**: `if wo.status ==
  'Open': wo.status = 'Released'` — reprinting an already-`Released` (or
  later-stage) WO does not re-trigger or downgrade anything.
- **`In Progress` — confirmed by Tebello (revision 2): leave unwired.**
  Verification finding stands: grepped every WO status write site in
  `routes/works_orders.py` (`mark_complete`, `confirm_pick`, `cancel_order`,
  `reopen_order`) — **nothing in the current code ever sets `'In Progress'`**,
  despite it already being a member of the existing `WO_ACTIVE` filter tuple
  since Batch 14. WOs today functionally jump `Open → Complete` (or
  `→ Cancelled`) directly; with this batch's `Released` addition, that
  becomes `Open → Released → Complete`, still skipping `In Progress`
  entirely. There is no natural partial-completion signal to hook it to —
  WOs (unlike STOs) have no incremental/partial issue mechanism, only the
  single all-at-once `mark_complete()` issue. **Confirmed, not built:**
  `In Progress` stays defined-but-unused for now (same as it already was
  before this batch). If Tebello wants it genuinely wired later, that's a
  small separate follow-up (a "Start Work" button that flips
  `Released → In Progress` with no other side effect).
- `WO_ACTIVE` (`services/order_filters.py`) gains `'Released'` — a
  WO that's been printed but not yet complete is still open work, same
  bucket it was already in as `'Open'` before this change, so this is not a
  new item appearing under the default `view=open` filter, just a status
  label refinement of items already showing there.
- **Template ripple, found by grep, must be updated everywhere the old
  2-value active list is hardcoded (not routed through `WO_ACTIVE`):**
  - `templates/works_orders/detail.html` lines 16, 21, 36, 43 — Edit/Mark
    Complete/Confirm Pick/Delete button availability, all currently gated on
    `['Open', 'In Progress']` or `== 'Open' or == 'In Progress'`.
  - `templates/works_orders/list.html` line 61 — Delete button availability,
    same `['Open', 'In Progress']` list.
  - All of the above need `'Released'` added to their allow-lists so a
    printed-but-not-started WO isn't accidentally locked out of Edit/Delete/
    Mark Complete.

#### Stock Order — `StockOrder.status` stays a stored column, gains a value, stays event-driven

New vocabulary: `Open → Released → Picking → Complete → Cancelled`. Same
"no schema change" finding as WO — `StockOrder.status` is a plain
`db.Column(db.String(50))`, no `CHECK` constraint.

- **`Released` (new)** — fires when the Picking List is printed.
  `stock_orders.py print_order()` is, like its WO counterpart, currently a
  pure render — same new-side-effect-on-a-GET-route note applies. Guarded to
  fire once: `if stock_order.status == 'Open': stock_order.status = 'Released'`.
- **`Picking` — verification finding, confirms these are already genuinely
  distinct moments, good news, no design conflict:** `pick_lines()`
  (`POST /stock-orders/<id>/pick`, `routes/stock_orders.py` line 161-162)
  already sets `status = 'Picking'` only once actual stock has been issued
  for at least one line (`any_picked` true) — this is a real, already-
  distinct "picking has actually started" event, separate from printing.
  Tebello's requirement ("Released and Picking should be genuinely distinct
  moments, not two names for one event") is **already satisfied by existing
  code** for the Picking half; only the Released half is new.
- **Required code changes to `pick_lines()` beyond adding the print-time
  flip:** the function's entry guard (line 113,
  `if stock_order.status not in ('Open', 'Picking')`) and its flip condition
  (line 161, `if stock_order.status == 'Open':`) both only recognize `'Open'`
  today — once `Released` exists, a printed-but-not-yet-picked STO would be
  sitting at `'Released'`, not `'Open'`, and picking must still be startable
  from there. Both need `'Released'` added: guard becomes
  `not in ('Open', 'Released', 'Picking')`, flip condition becomes
  `in ('Open', 'Released')`.
- `STO_ACTIVE` gains `'Released'` — same "already-open, just relabeled"
  reasoning as WO.
- **Template ripple, found by grep — confirmed, implement (revision 2):**
  `templates/stock_orders/detail.html` lines 19, 84, 95, 117, 132 all
  hardcode `stock_order.status in ['Open', 'Picking']` (Mark Complete/
  Cancel availability, pick-form rendering at multiple points on the page)
  — all need `'Released'` added, or the pick form and Cancel button would
  disappear for a printed-but-unpicked STO. **Line 16
  (`stock_order.status == 'Open'`, gates the Edit link) — confirmed by
  Tebello (revision 2), not just a recommendation:** extend to also allow
  Edit from `Released` (`stock_order.status in ['Open', 'Released']`),
  since editing lines before picking starts is still safe. 6 sites total,
  all now confirmed, not flagged.

---

## Decision 2 (locked in) — Event-driven Change Log is in scope

New model, following SOPS's `StockMovement`-style naming and its precedent
of a plain string reference instead of a strict FK for records that can
point at more than one parent table:

```python
class StatusChangeLog(db.Model):
    __tablename__ = 'status_change_log'
    id = db.Column(db.Integer, primary_key=True)
    order_type = db.Column(db.String(10), nullable=False)   # 'SO' / 'WO' / 'STO'
    order_id = db.Column(db.Integer, nullable=False)         # PK into sales_order/works_order/stock_order — not FK-enforced (polymorphic across 3 tables, same convention as StockMovement.reference)
    order_number = db.Column(db.String(100))                 # denormalized so_number/wo_number/stock_order_number, so the Change Log report doesn't need a per-row join
    field_name = db.Column(db.String(50), nullable=False)    # see tracked-field list below
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.now)
    changed_by = db.Column(db.String(255))                    # optional; 'System' where no explicit actor is known, mirrors stock_service's convention
```

**Trigger: event-driven**, written by the service layer at the moment each
tracked field changes — not a periodic diff/snapshot job.

**Tracked fields (fixed list, per Tebello — not a full row snapshot; revised
per Decision 3 below — `total_override`/`display_total` dropped,
`amount_paid` added since it's now the field that actually drives the
export's `Total` via `balance_due`):**
- SO `report_status` (derived — see below), `on_hold`/`on_hold_reason`,
  `payment_status`, `amount_paid`, `delivery_date`, `report_notes`.
- WO `status`.
- STO `status`.

**How `report_status` gets logged despite having no setter:** since it's a
computed property, there's nothing to intercept directly. Design: a small
context manager in the new `services/status_change_log.py`, used to wrap
every route block that can change a WO/STO/SO status (`build_bom()`,
WO `print_order`/`mark_complete`/`cancel_order`/`reopen_order`, STO
`print_order`/`pick_lines`/`complete_order`/`cancel_order`/`reopen_order`):

```python
from contextlib import contextmanager

@contextmanager
def track_report_status(so):
    before = so.report_status
    yield
    after = so.report_status
    if before != after:
        log_change('SO', so.id, so.so_number, 'report_status', before, after)
```

Used as `with track_report_status(so): <existing route logic>` around
whatever WO/STO/SO mutation is already happening in that route — the
context manager snapshots `so.report_status` before and after the wrapped
block and writes a `StatusChangeLog` row only if the computed value actually
changed. This means every route touching WO/STO status also needs the
owning `SalesOrder` fetched (already true in every case checked — each of
these routes already has `wo.sales_order` / `stock_order.sales_order`
available).

Each direct-column change (`WO.status`, `STO.status`, `on_hold`,
`payment_status`, `amount_paid`, `delivery_date`, `report_notes`) gets a
plain `log_change(...)` call at its existing route/service call site — no
context manager needed there since there's a real before/after value to
diff directly.

**Scope: only the fields above** — not a full SO/WO/STO row snapshot.
Explicitly rejected by Tebello as overkill; keeps the log table small and
the Change Log report's rows meaningful (one row = one real, human-relevant
change).

**Access — Change Log report, not a timeline or an export:**
`GET /reports/change-log` (page) + `GET /reports/change-log/data` (JSON,
Tabulator-backed, same pattern as the existing Stock/Movement reports in
`routes/reports.py`) — one report listing every tracked change across every
order in a date range, filterable by date range and (recommended, not
explicitly requested — flagged) order type / field name. **Not** a per-order
timeline view and **not** a point-in-time Excel export — both considered by
Tebello and explicitly rejected, not built here. No CSV export button added
either (the other two reports both have one) — Tebello didn't ask for it and
it's easy to add later; flagged as a deliberate omission, not a silent gap.

---

## Decision 3 (final, substantially revised) — Total column uses `balance_due`; `total_override` dropped entirely

**Investigation requested by Tebello (revision 2):** the original spec's
open question treated the old pipeline's 2-job Total correction
(FM4047/FM4164) as a possible Sage source-data bug. Tebello's exact
correction: "it is not a bug, it is the totals minus paid as they are
partially paid."

**Verified against the real code (`models.py` lines 55, 69, 73-74):**

```python
amount_paid = db.Column(db.Float, default=0.0)  # only read/written/displayed when payment_status == 'Cash Sale - Partial'
...
@property
def total_incl(self):
    return sum(li.incl_total or 0 for li in self.line_items)

@property
def balance_due(self):
    return self.total_incl - (self.amount_paid or 0.0)
```

**`balance_due` already computes exactly "total minus paid"** — this is the
identical calculation the old pipeline's manual edit was reproducing by
hand for those 2 jobs, every single day. For any SO where `amount_paid` is
still `0.0` (its default — true for every non-`Cash Sale - Partial` SO,
since that field is only ever written when the status is Partial), 
`balance_due == total_incl`, so using `balance_due` as the export's `Total`
column is a strict generalization, not a behavior change, for every SO
outside the partial-payment case.

**Decision: drop `total_override`/`display_total` entirely.** The export's
`Total` column sources `so.balance_due` directly — no new column, no
override input, no escape-hatch field. Reasoning:
- The one concretely-known need for a manual total correction (the 2
  partially-paid jobs) is **already solved** by existing, shipped
  functionality (`balance_due`, Batch 24) — building a parallel
  `total_override` mechanism would be solving an already-solved problem
  with more state to keep consistent, exactly the kind of redundancy
  Tebello flagged as a concern.
- There's no other concrete, currently-known case requiring a manual total
  correction unrelated to payment (e.g. a genuinely wrong PDF-parsed line
  item) — building speculative machinery for a hypothetical is against this
  project's YAGNI convention elsewhere in the codebase (e.g. Batch 19's
  removal of the CSV quantity-overwrite toggle for a similar reason).
  If a real "the line-item total itself is wrong, unrelated to payment"
  need surfaces later, that's a distinct, narrower feature to scope then —
  not built preemptively here.
- Because `total_override` never existed in shipped code (this spec was
  revised before any Executor touched it), dropping it costs nothing —
  no migration to reverse, no data to migrate away from.

**Ripple from dropping `total_override`:**
- `models.py`: no `total_override` column, no `display_total` property.
- `scripts/migrate_add_so_report_fields.py`: now adds exactly 3 columns
  (`report_notes`, `on_hold`, `on_hold_reason`), not 4.
- No `update_total_override()` route, no Total Override row on the SO
  detail page template (the existing Total row + the existing conditional
  Balance Due row from Batch 24 already communicate everything needed —
  nothing new to add there).
- `services/sales_order_report_export.py`: `Total` column reads
  `so.balance_due`, not `so.display_total`.
- `StatusChangeLog` tracked-field list: `total_override`/`display_total`
  replaced with `amount_paid` (see Decision 2) — `amount_paid` is the field
  that actually drives a `Total`-relevant change now.

**The original `report_notes` design and the `save_order()`
overwrite-carry-forward fix are still needed and still correct** — kept as
designed. `report_status` stays dropped from that list (computed property,
nothing to carry forward). **Caveat, still true:** `save_order()`'s
overwrite path is already blocked entirely whenever a WO or STO is linked
(`routes/sales_orders.py` lines ~108-119), so "overwriting an SO that
already has WOs/STOs" can never occur — confirmed consistent.

**`on_hold`/`on_hold_reason` need the same overwrite-path protection** —
manually-set fields with no competing automated writer, exactly like
`report_notes`. Added to the `save_order()` carry-forward fix's scope.

**New in this revision — `amount_paid` pulled into the same carry-forward
fix, deliberate small scope expansion:** re-reading `save_order()`
(`routes/sales_orders.py` ~lines 135-149) confirms the `SalesOrder(...)`
constructor call on overwrite never sets `amount_paid` at all — it silently
resets to the column default (`0.0`) on every overwrite, unconditionally.
This was flagged in the original draft as a **pre-existing, out-of-scope**
gap. It is being **pulled into scope now** rather than left deferred,
because — now that the export's `Total` column is `balance_due`, which
depends directly on `amount_paid` — that pre-existing gap would silently
undermine this batch's own core purpose (an accurate Total column) the
moment someone re-uploads a PDF for a `Cash Sale - Partial` SO that hasn't
reached Build Works Pack yet. This is a one-line addition to an
already-planned fix (one more field captured before
`db.session.delete(existing)`, alongside `report_notes`/`on_hold`/
`on_hold_reason`), not a new file or a new task.

**Final carry-forward field list:** `report_notes`, `total_override`
~~dropped~~, `on_hold`, `on_hold_reason`, `amount_paid` — i.e. before
`db.session.delete(existing)` in `save_order()`, capture
`existing.report_notes` / `on_hold` / `on_hold_reason` / `amount_paid` and
re-apply them onto the new `so` object before commit.

Reasoning for why no field-level allowlist machinery is needed (unchanged
from the original draft): none of these fields has a competing automated
writer anywhere in SOPS (PDF parser, invoice importer, `build_bom()` all
leave them untouched) — the only risk is the one-off `save_order()`
overwrite event, now fully covered by the fix above.

**No open questions remain in this Decision** — the 2-job Total-correction
question is resolved (it was `balance_due`'s job all along, not a separate
mechanism), not deferred.

---

### Decision 4 — `CustomerInvoicesReport.csv` importer + new `Invoice` model (unchanged)

No changes. New `Invoice` model (no FK to `SalesOrder`, deliberately — see
original reasoning), `services/invoice_importer.py`
`import_invoices_from_csv()` (full upsert by `invoice_number`, no competing
manual field), upload-only `GET/POST /sales-orders/import-invoices` route.

---

### Export design — `services/sales_order_report_export.py` (final)

Same two-sheet structure as the original draft.

**Sheet 1 — "Sales Order Report":**
- `Status` column reads `so.display_report_status` (computed, includes the
  On Hold overlay). A SO whose `report_status` is `None` (Closed/Cancelled)
  is excluded from the default `?view=open` export anyway (via `SO_ACTIVE`
  filtering); the `None` case only matters for a `?view=all` pull — render
  as `'-'` there.
- `Total` column reads **`so.balance_due`** (not `total_incl`, not a
  dropped `display_total`) — see Decision 3. For any SO outside the
  `Cash Sale - Partial` case this is numerically identical to `total_incl`
  (since `amount_paid` defaults to `0.0`), so this is a pure generalization,
  not a behavior change, for the vast majority of rows.
- All other columns unchanged: `Job Number` = `so.job_numbers` (multi-fan
  edge case flagged below, unchanged), `Payment Status` =
  `so.payment_status`, `Notes` = `so.report_notes`.
- Summary block (Total Value, Breakdown, Due-Today, Ready-Dispatch total)
  — still computed in Python from the same in-memory SO list. **Note:**
  these summary totals should also sum `balance_due` rather than
  `total_incl`/raw `Total`, for the same reason the per-row column does —
  otherwise the Breakdown/Due-Today totals would disagree with the
  per-row Total shown just above them.

**Sheet 2 — "Monthly INV - MM.YYYY":** unchanged from the original draft
(sourced from the `Invoice` table's own `Exclusive`/`Total Selling` figures,
not from `SalesOrder`, so `balance_due` doesn't apply there).

**Route** (`GET /sales-orders/export-excel`): `?view=open|all`,
**`?view=open` confirmed as the default** (not just recommended — see
Confirmed-by-Tebello #9), matching Batch 16/21's list-page convention. Same
filename convention, same content type. No dependency on `StatusChangeLog`
in the export itself — the Change Log lives in its own report page, per
Decision 2.

**UI additions:**
- SO detail page: `Report Status` row becomes **read-only display**
  (`so.display_report_status`) — no dropdown, since it's computed. A
  separate **On Hold** toggle (checkbox/button, optional reason textarea)
  gets its own inline form, `POST /sales-orders/<id>/on-hold`, mirroring the
  existing Payment Status/Delivery Date inline-edit pattern. **No Total
  Override UI** — dropped per Decision 3; the existing Total row + the
  existing conditional Balance Due row (Batch 24) already cover this.
- WO/STO badges gain a `.badge-released` CSS rule
  (`static/css/main.css`), matching the existing `.badge-picking`/
  `.badge-inprogress` precedent from Batch 23 — badge slug already derives
  generically via `status.lower().replace(' ', '')`, so `'Released'` needs
  no special-casing there, just the new CSS rule.

---

### Schema changes — migration plan (flagged to Architect, final)

**Three migration scripts required:**

1. `scripts/migrate_add_so_report_fields.py` — adds `report_notes`,
   `on_hold`, `on_hold_reason` to the existing `sales_order` table (3
   columns, not 4 — `total_override` dropped per Decision 3;
   `report_status` was never a column). Matching `ensure_schema_columns()`
   self-heal entries in `app.py` for all 3.
2. `scripts/migrate_add_invoice_table.py` — unchanged from the original
   draft.
3. `scripts/migrate_add_status_change_log_table.py` — creates the
   `status_change_log` table via `db.create_all()`, same convention as the
   `Invoice`/`PurchaseOrder`/`Setting` table migrations (no self-heal entry
   needed — that mechanism is for adding columns to existing tables, and
   `db.create_all()` on every app startup already covers brand-new tables).

**No migration needed for `WorksOrder.status`/`StockOrder.status` gaining
the `'Released'` value** — confirmed both are plain `db.Column(db.String(50))`
with no `CHECK` constraint, so a new string value is a pure code-level
change (routes + `order_filters.py` + template conditionals + CSS), not a
schema change.

**None of the three scripts is to be run against `instance/sops.db` by the
Executor** — held for Tebello's go-ahead, same standing convention as every
prior schema-change batch (24, 26, 32, 33).

---

### Sequencing (SOPS-side atomic commits, for the Orchestrator/Executor — final)

1. `models.py` — `Invoice` model; `SalesOrder`: `on_hold`/`on_hold_reason`
   columns (no `total_override`), `report_status` (all-complete logic) and
   `display_report_status` computed properties; new `StatusChangeLog`
   model. Drop the old `SO_REPORT_STATUS_OPTIONS` tuple (no dropdown to
   validate against).
2. `scripts/migrate_add_so_report_fields.py` (3 columns, see above) +
   `app.py` self-heal entries.
3. `scripts/migrate_add_invoice_table.py` (unchanged).
4. `scripts/migrate_add_status_change_log_table.py` (unchanged).
5. `services/status_change_log.py` (`log_change()` + `track_report_status()`
   context manager) + `tests/test_status_change_log.py`.
6. `services/invoice_importer.py` + `tests/test_invoice_importer.py`
   (unchanged).
7. `routes/sales_orders.py` `import_invoices()` route +
   `templates/sales_orders/import_invoices.html` (unchanged).
8. `routes/sales_orders.py` `update_report_notes()` route +
   `templates/sales_orders/detail.html` Notes row (unchanged).
9. `routes/sales_orders.py` — `save_order()` overwrite-carry-forward fix,
   final field list: `report_notes`, `on_hold`, `on_hold_reason`,
   `amount_paid` (the last one newly pulled into scope this revision — see
   Decision 3) + `tests/test_so_report_fields.py` (carry-forward regression
   test covering all 4 fields).
10. `routes/sales_orders.py` new `update_on_hold()` route +
    `templates/sales_orders/detail.html` On Hold toggle UI + read-only
    computed Report Status row (`display_report_status`).
11. `routes/sales_orders.py` `build_bom()` — wrap WO/STO creation in
    `track_report_status(so)`, log the initial `status='Open'` creation
    event for each new WO/STO (`old_value=None`) + `tests/test_status_change_log.py`
    (extended).
12. `services/order_filters.py` — `WO_ACTIVE`/`STO_ACTIVE` gain `'Released'`
    + `tests/test_order_list_filters.py` (updated assertions covering the
    new value under `view=open`/`view=closed`).
13. `routes/works_orders.py` — `print_order()` Released-flip (guarded,
    fires once), `StatusChangeLog` calls at print/`mark_complete`/
    `cancel_order`/`reopen_order`, wrapped in `track_report_status()` where
    the owning SO's computed status could change + `templates/works_orders/detail.html`
    (4 conditional sites updated to include `'Released'`).
14. `templates/works_orders/list.html` (1 conditional site updated) +
    `static/css/main.css` (`.badge-released` rule).
15. `routes/stock_orders.py` — `print_order()` Released-flip, `pick_lines()`
    guard/flip-condition updates (`'Released'` added to both),
    `StatusChangeLog` calls at print/`complete_order`/`cancel_order`/
    `reopen_order`, wrapped in `track_report_status()` +
    `templates/stock_orders/detail.html` (6 conditional sites updated,
    including the now-confirmed Edit-from-`Released` allowance at line 16).
16. `routes/sales_orders.py` — add `log_change()` calls to the existing
    `update_payment_status()` (now logging both `payment_status` and
    `amount_paid` when either changes) and `update_delivery_date()` routes
    (no template change needed, these routes already exist).
17. `tests/test_so_report_fields.py` — extended: `report_status` computed
    correctly for `Loaded`/`Released`/`Ready-Dispatch` under the *all*-based
    rule, including the all-`Cancelled`-doesn't-count-as-`Ready-Dispatch`
    edge case and a multi-WO partial-complete-stays-`Released` case; `None`
    for Closed/Cancelled; `on_hold` round-trip; `display_report_status`
    formatting; `balance_due` sanity check (`total_incl` when
    `amount_paid == 0`, netted correctly when `Cash Sale - Partial`);
    `save_order()` overwrite-carry-forward covers all 4 fields (item 9
    above).
18. `services/sales_order_report_export.py` — workbook builder; `Status`
    column sources `so.display_report_status`, `Total` column and summary
    sums source `so.balance_due`.
19. `routes/sales_orders.py` `export_excel()` route (default
    `?view=open`, confirmed) + `templates/sales_orders/list.html` (Export
    Excel button + read-only computed Report Status column + On Hold
    indicator).
20. `tests/test_sales_order_report_export.py` — export route + workbook
    content tests, including a `Cash Sale - Partial` fixture SO asserting
    the exported `Total` equals `balance_due`, not `total_incl`.
21. `routes/reports.py` `change_log()`/`change_log_data()` routes +
    `templates/reports/change_log.html` (new Change Log report page).
22. `templates/base.html` — nav entry for the Change Log report.
23. `tests/test_change_log_report.py` — new tests for the change-log
    listing route and its date-range/order-type/field-name filters.
24. Full suite green; offline-first re-verified; no new dependency
    (openpyxl already pinned).

---

### Tests required (final)

- `test_status_change_log.py`: `log_change()` writes a correct row;
  `track_report_status()` writes a row only when the computed value actually
  differs before/after, writes nothing when it doesn't; `build_bom()`
  creation logs the initial WO/STO `status` events and the resulting SO
  `report_status` Loaded→Released transition in one call.
- `test_order_list_filters.py`: `'Released'` WOs/STOs appear under
  `view=open`, not under `view=closed`, for both WO and STO.
- `test_works_orders.py` / `test_stock_orders.py` (extended): `print_order()`
  flips `Open → Released` exactly once (reprinting doesn't re-flip or log a
  no-op change); STO `pick_lines()` works correctly starting from `Released`
  (not just `Open`); STO Edit link is available from `Released` (new,
  confirmed); all 4 WO / 6 STO template-conditional sites render correctly
  for a `Released` order (Edit/Delete/Mark Complete/Cancel/pick form all
  still available, not silently hidden).
- `test_so_report_fields.py` (extended): see Sequencing item 17 above —
  includes the *all*-based `Ready-Dispatch` logic and its edge cases, plus
  `balance_due`/carry-forward coverage.
- `test_sales_order_report_export.py`: `Status` column reflects
  `display_report_status` including the On Hold overlay; a `Ready-Dispatch`
  SO (all linked orders Complete) and a `Loaded` SO both render correctly;
  a partially-complete multi-WO SO renders `Released`, not
  `Ready-Dispatch`; a `Closed` SO (via `?view=all`) renders `'-'` for
  Status rather than erroring; `Total` column equals `balance_due` for a
  `Cash Sale - Partial` fixture SO, not the gross `total_incl`.
- `test_change_log_report.py`: a mix of SO/WO/STO field changes produces the
  correct rows; date-range filter narrows correctly; order-type/field-name
  filters narrow correctly; no full-row-snapshot fields (e.g. `customer_name`)
  ever appear as a `field_name` — only the fixed tracked list does.

---

### Acceptance criteria (final)

- [ ] `report_status` is never a stored/editable value anywhere in the UI —
      confirmed via `grep -rn "report_status" templates/` showing only
      read-only render sites, no `<select>`/`<input>`.
- [ ] `report_status` correctly requires **all** linked WOs/STOs to be
      terminal (`Complete`/`Cancelled`) with **at least one** actually
      `Complete` before returning `Ready-Dispatch` — an all-`Cancelled` set
      does not qualify.
- [ ] `On Hold` is toggleable only at the SO level; no On Hold control exists
      on any WO or STO template.
- [ ] WO `Released` and STO `Released` both fire exactly once, on first
      print, verified not to re-fire or regress on a later reprint.
- [ ] STO `Picking` still fires only on an actual pick action (unchanged
      behavior, re-verified after the `Released`-related guard changes).
      STO Edit is available from both `Open` and `Released`.
- [ ] No `total_override` column, property, route, or template field exists
      anywhere — confirmed via `grep -rn "total_override\|display_total"`
      returning empty across the whole repo.
- [ ] The export's `Total` column and summary totals both use `balance_due`,
      matching the SO detail page's existing Total/Balance Due display for
      the same order.
- [ ] `StatusChangeLog` gains a row for every tracked-field change exercised
      in the test suite above, and only for those fields — no
      full-row-snapshot data leaks into the log.
- [ ] `GET /reports/change-log` renders a filterable table of all logged
      changes; no per-order timeline view or Excel export exists for this
      data.
- [ ] `Invoice` table + `sales_order` columns (`report_notes`, `on_hold`,
      `on_hold_reason`) + `status_change_log` table all exist via migration
      scripts (not yet run against `instance/sops.db` — held for Tebello).
- [ ] Re-uploading a PDF for an existing SO (overwrite path, no linked
      WO/STO — the only path where this scenario can occur, per Decision 3)
      preserves `report_notes`/`on_hold`/`on_hold_reason`/`amount_paid`.
- [ ] `GET /sales-orders/export-excel` defaults to `?view=open`, produces a
      2-sheet workbook with `Status` reflecting the computed value + On
      Hold overlay and `Total` reflecting `balance_due`.
- [ ] No route/service in this batch reads from or writes to the OneDrive
      Contract Register or Released Jobs PDF paths.
- [ ] Offline-first re-verified; no new package added.
- [ ] `pytest` full suite green.

---

### Out of scope

- Decommissioning or modifying the standalone `1. Daily Sales Order Files`
  pipeline (constraint 2).
- Any read/write access to the OneDrive Contract Register or Released Jobs
  PDF folders (constraint 4).
- Per-job-number export granularity for multi-fan SOs with distinct FM
  numbers per line (flagged edge case, not solved).
- Automated Sage/bank payment reconciliation for any of the new fields.
- Linking `Invoice` rows back to specific `SalesOrder` records.
- A per-order-timeline view or a point-in-time Excel export of change
  history — both explicitly considered and rejected by Tebello in favor of
  the single Change Log report (Decision 2).
- CSV export button on the Change Log report — easy follow-up, not
  requested, not built now.
- Wiring a real `In Progress` transition for Works Orders — confirmed
  staying unwired (Decision 1).
- A general-purpose `total_override` escape hatch for a hypothetical
  "genuinely wrong line-item total unrelated to payment" — not a currently
  known need; `balance_due` covers the one concretely-known case. If a real
  need surfaces later, scope it as its own small feature then.
