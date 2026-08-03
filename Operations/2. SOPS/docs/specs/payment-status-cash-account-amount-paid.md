## Task: Payment Status restructure (Cash Sale / Account prefixes) + Amount Paid for partial payments

**Domain:** Software / AI
**Date:** 2026-07-14
**Requested by:** Tebello

**Goal:** Replace the flat `PAYMENT_STATUS_OPTIONS` list with a two-category (Cash Sale / Account) list, add `Account - Overdue`, and add an "Amount Paid" field that applies specifically to the `Cash Sale - Partial` status so the SO detail page can show a computed Balance Due.

**Decisions confirmed with Tebello (2026-07-14, via AskUserQuestion):**
1. **New option list (exact, as given):**
   `Cash Sale - Unpaid`, `Cash Sale - Paid`, `Cash Sale - Partial`, `Account - On Hold`, `Account - Up to Date`, `Account - Pending`, `Account - Overdue` (7 total — Overdue confirmed as an addition on top of the 6 originally listed).
2. **Amount field:** a single `Amount Paid` number. Balance Due is computed (`SalesOrder.total_incl - amount_paid`), not entered separately.
3. **Scope:** Amount Paid only shows/applies when `payment_status == 'Cash Sale - Partial'` — not tracked for other statuses.
4. **Entry point:** SO detail page only (same place the existing Payment Status dropdown lives) — not added to the upload/review intake form.
5. **Existing production data:** best-guess auto-map old → new values via a one-off migration script, with the ambiguous mappings printed out for Tebello to spot-check afterward (see mapping table below).

---

### Model changes — `models.py`

**Line 27** — `PAYMENT_STATUS_OPTIONS`:
```python
PAYMENT_STATUS_OPTIONS = (
    'Cash Sale - Unpaid', 'Cash Sale - Paid', 'Cash Sale - Partial',
    'Account - Pending', 'Account - Up to Date', 'Account - On Hold', 'Account - Overdue',
)
```
Order matches the grouping Tebello gave (Cash Sale block, then Account block) — this is also the order the `<select>` renders in.

**Line 44** — `SalesOrder.payment_status` default changes from `'Pending'` (no longer a valid value) to `'Account - Pending'` (closest semantic equivalent — flagged here for Tebello to override if a different default is preferred; not blocking since it only affects brand-new Sales Orders going forward, not existing data).

**New column** — `SalesOrder.amount_paid = db.Column(db.Float, default=0.0)`. Always present (simplifies the column set — no nullable-vs-zero ambiguity), but only ever read/written/displayed when `payment_status == 'Cash Sale - Partial'`.

**New computed property**, mirroring the existing `total_incl` pattern (models.py:57-59):
```python
@property
def balance_due(self):
    return self.total_incl - (self.amount_paid or 0.0)
```

**New migration** — `scripts/migrate_add_payment_status_amount_paid.py` (schema: add `amount_paid` column) + matching `ensure_schema_columns()` self-heal entry in `app.py`, per the hard rule (no schema change without a migration file).

---

### Data migration — existing Sales Orders' `payment_status` values

**New one-off script** — `scripts/migrate_payment_status_values.py`. Mapping table:

| Old value | New value | Confidence |
|---|---|---|
| `Account - Up to Date` | `Account - Up to Date` | Direct match, unchanged |
| `On Hold` | `Account - On Hold` | Direct match, prefix added |
| `Partially Paid` | `Cash Sale - Partial` | Direct match — only partial-payment status in the new list |
| `Pending` | `Account - Pending` | **Guess** — no record of whether it was ever a cash sale |
| `Paid` | `Cash Sale - Paid` | **Guess** — could equally have been `Account - Up to Date` |
| `Unpaid` | `Cash Sale - Unpaid` | **Guess** — could equally have been an overdue/pending account |
| *(anything else / null)* | `Account - Pending` | Fallback default |

Behavior:
- Idempotent/safe to re-run: skips any `SalesOrder` whose `payment_status` is already one of the 7 new values (so re-running after Tebello manually corrects a guessed one won't clobber the correction).
- `Partially Paid → Cash Sale - Partial` rows get `amount_paid` left at `0.0` — there's no historical record of how much was actually paid, so Tebello will need to fill in the real amount manually via the new detail-page field for any of these that still matter.
- Prints a summary at the end: count mapped per old value, and an explicit list of SO numbers whose mapping fell into one of the three **Guess** rows above, so Tebello can review just those rather than the whole table.
- Run once, manually, against `instance/sops.db` (matches the project's existing one-off-script convention, e.g. the 2026-07-10 test-data purge) — not part of `ensure_schema_columns()` self-heal, since it's a data transform, not a schema addition.

---

### `routes/sales_orders.py`

**`update_payment_status()` (line 556-570)** — extend to also accept/validate `amount_paid` when the submitted status is `Cash Sale - Partial`:
```python
new_status = request.form.get('payment_status', '').strip()
if new_status not in PAYMENT_STATUS_OPTIONS:
    flash(f"Invalid payment status: {new_status}", "error")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))

if new_status == 'Cash Sale - Partial':
    amount_raw = request.form.get('amount_paid', '').strip()
    try:
        so.amount_paid = float(amount_raw) if amount_raw else (so.amount_paid or 0.0)
    except ValueError:
        flash("Amount Paid must be a number.", "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

so.payment_status = new_status
db.session.commit()
```
Validate before mutating `so` so an invalid amount doesn't leave the status half-changed. `amount_paid` is intentionally **not reset** when moving away from `Cash Sale - Partial` — it just stops being displayed/relevant (see template below); this avoids losing the figure if the status is toggled back and forth.

**`upload_order()` / `save_order()` (lines ~89, ~95, ~147, ~188)** — no change beyond automatically picking up the new `PAYMENT_STATUS_OPTIONS` values through the existing `payment_status_options=PAYMENT_STATUS_OPTIONS` template variable already threaded through both the GET and POST paths. Per the "SO detail page only" decision, the intake form gets no Amount Paid field.

---

### `templates/sales_orders/detail.html`

**Line 80** — add a Balance Due row directly after the existing Total row, shown only when relevant:
```html
{% if so.payment_status == 'Cash Sale - Partial' %}
<tr><td class="detail-label">Balance Due</td><td class="detail-value">R {{ '%.2f'|format(so.balance_due) }}</td></tr>
{% endif %}
```

**Lines 82-89 (existing Payment Status form)** — add an Amount Paid input inside the same `<form>`, rendered only when the *current* status is `Cash Sale - Partial` (the page re-renders after every status change since the dropdown auto-submits via `onchange="this.form.submit()"`, so this conditional naturally reflects the just-saved value with no extra JS needed):
```html
<form method="POST" action="{{ url_for('sales_orders.update_payment_status', order_id=so.id) }}" style="display: flex; gap: 8px; align-items: center;">
    <select name="payment_status" class="form-input" style="width: auto; padding: 4px 8px; font-size: 0.85rem;" onchange="this.form.submit()">
        {% for option in payment_status_options %}
        <option value="{{ option }}" {{ 'selected' if so.payment_status == option else '' }}>{{ option }}</option>
        {% endfor %}
    </select>
    {% if so.payment_status == 'Cash Sale - Partial' %}
    <input type="number" name="amount_paid" value="{{ so.amount_paid or 0 }}" step="0.01" min="0"
           class="form-input" style="width: 100px; padding: 4px 8px; font-size: 0.85rem;" placeholder="Amount paid">
    <button type="submit" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;">Update</button>
    {% endif %}
</form>
```
Note: changing the `<select>` still auto-submits immediately (existing behavior, unchanged) — it will submit whatever's currently in the Amount Paid box too, which is harmless since the route only reads `amount_paid` when the *submitted* status is `Cash Sale - Partial`. The new "Update" button exists for the case where Tebello wants to update just the amount without touching the status dropdown.

### `templates/sales_orders/list.html`

**Line 52** — no change. Payment Status already renders as plain text (`{{ so.payment_status or '-' }}`), not a badge, so the longer new values with spaces/hyphens don't hit any CSS-class-slug issue.

### `templates/sales_orders/upload.html`

No change — the existing Payment Status `<select>` there already iterates `payment_status_options`, so it picks up the new 7-value list automatically.

---

### Sequencing (atomic commits)

1. `models.py` — new `PAYMENT_STATUS_OPTIONS`, `amount_paid` column, `balance_due` property, default value update.
2. `scripts/migrate_add_payment_status_amount_paid.py` + `ensure_schema_columns()` self-heal entry.
3. `scripts/migrate_payment_status_values.py` (data migration, run once against `instance/sops.db`, output reviewed before committing the script but the script itself is committed for reproducibility/audit).
4. `routes/sales_orders.py` `update_payment_status()` — Amount Paid read/validate.
5. `templates/sales_orders/detail.html` — Balance Due row + Amount Paid input + Update button.
6. Tests + full suite green.

**New/updated tests (`tests/test_so_report_fields.py`):**
- `PAYMENT_STATUS_OPTIONS` contains exactly the 7 new values in the specified order; none of the 6 old bare values are present.
- `update_payment_status()` accepts `Cash Sale - Partial` + a valid `amount_paid`, persists both.
- `update_payment_status()` rejects a non-numeric `amount_paid` when status is `Cash Sale - Partial` — flashes an error, leaves `so.payment_status`/`so.amount_paid` unchanged.
- `update_payment_status()` on any non-Partial status ignores a submitted `amount_paid` (doesn't error, doesn't overwrite the stored value).
- `SalesOrder.balance_due` computes `total_incl - amount_paid` correctly, including the `amount_paid=0.0` default case (balance_due == total_incl).
- Data migration script (run against an in-memory fixture DB): direct-match rows map exactly as specified; ambiguous rows map to their documented guess; a row already on a new-list value is left untouched on a second run (idempotency check).

**Acceptance criteria:**
- [ ] Payment Status dropdown (upload/review form and SO detail page) shows exactly the 7 new Cash Sale / Account values, correctly grouped/ordered.
- [ ] Selecting `Cash Sale - Partial` reveals an Amount Paid field; entering a value and updating shows a correct Balance Due on the SO detail page.
- [ ] Switching away from `Cash Sale - Partial` hides the Amount Paid field and Balance Due row (value is retained in the DB, just not surfaced).
- [ ] An invalid (non-numeric) Amount Paid is rejected with a flash message, no partial save.
- [ ] Existing Sales Orders have been migrated to one of the 7 new values (verified via the migration script's printed summary); Tebello has reviewed the flagged ambiguous ones.
- [ ] `pytest` full suite green.

**Out of scope:**
- Amount Paid / Balance Due for any status other than `Cash Sale - Partial`.
- Adding Amount Paid to the upload/review intake form.
- Any automated bank/Sage payment reconciliation — this remains a manually-typed figure, same trust level as the Payment Status dropdown itself.
- Retroactively determining the *real* historical amount paid for existing `Cash Sale - Partial`-mapped orders (defaults to 0, manual fill-in only).
