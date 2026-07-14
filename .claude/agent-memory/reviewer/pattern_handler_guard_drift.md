---
name: pattern-handler-guard-drift
description: Sibling order-transition handlers in SOPS routes guard status inconsistently, and shared templates get context vars added to one render path but not another.
metadata:
  type: project
---

SOPS order-lifecycle routes come in near-duplicate families (Works Order / Stock Order / Sales Order / Purchase Order each have complete/cancel/reopen/edit handlers, plus WO has both `mark_complete` and `confirm_pick`). These siblings tend to drift in their guard clauses and in the context they hand to a shared template.

Confirmed instances (2026-07-14):
- `routes/works_orders.py::confirm_pick()` guards only `status == 'Complete'`, while its sibling `mark_complete()` guards BOTH `'Complete'` and `'Cancelled'`. A cancelled STOCK works order POSTed straight to `/confirm-pick` would issue stock and flip to Complete (un-cancelling it). Not reachable via the detail-page button (shown only for Open/In Progress), so it's a defense-in-depth / drift gap, not a live UI bug.
- `routes/sales_orders.py::reupload_order()` (both GET ~line 691 and POST ~line 680) render `sales_orders/upload.html` WITHOUT `payment_status_options`, but `upload_order()` passes it and the template iterates it unconditionally (`{% for option in payment_status_options %}`, upload.html:79). Default Jinja Undefined raises on iteration → the whole re-upload flow 500s.

**Why:** These handlers are copy-adapted from each other; when one gets a new guard or a new template var, the twin is easy to miss. The reupload/upload split is the same class as the Batch 16 view-toggle bug (one path updated, its pair not).

**How to apply:** When reviewing any change to one order-transition handler, open its siblings in the same file AND the parallel routes and diff the guard clauses + the render_template kwargs. For any template rendered from >1 route, confirm every render site passes the same context keys the template consumes.
