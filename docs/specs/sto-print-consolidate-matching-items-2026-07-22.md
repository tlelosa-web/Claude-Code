# Spec — Consolidate matching items on the printed Stock Order (STO)

**Date:** 2026-07-22
**Owner:** Tebello Lelosa
**Type:** Small feature (print-only display change)
**Status:** Implemented 2026-07-22 — full suite green (335 passed, incl. 4 new cases)

-----

## Problem

When the same catalogue item appears on more than one line of a Stock Order
(common with multi-fan builds, where the same component is pulled in once per
fan), the printed STO renders each occurrence as its own row. The stores
department gets a picking sheet with duplicate item lines instead of one line
per item with a combined quantity.

Current print template loops `stock_order.lines` directly
(`templates/stock_orders/print.html:79`), one `<tr>` per stored line.

## Decision (confirmed with Tebello 2026-07-22)

- **Print-only merge.** Only the printed STO consolidates. The stored
  `StockOrderLine` rows, the detail/edit screens, the per-line picking flow,
  and stock deduction are all left untouched. This keeps `qty_issued`
  per-line accounting and `issue()` stock integrity exactly as they are.
- **Match rule:** group by `item_code`. Blank/None item codes are **never**
  merged — each blank-code line stays its own row.
- **Notes:** distinct non-empty `notes` from the merged lines are joined into
  one cell (`; ` separator). Description is assumed identical across a group;
  take the first non-empty one.

## Approach

### 1. Route helper — `routes/stock_orders.py`

Add a module-level helper mirroring the existing `_line_extras` pattern
(no logic in the route handler itself):

```python
def _consolidate_print_lines(stock_order):
    """Group Stock Order lines by item_code for the printed STO, summing qty
    and joining distinct notes. Blank item_codes are never merged — each such
    line stays its own row. Print-only: stored StockOrderLine rows, picking,
    and stock deduction are unaffected. Row order follows each item_code's
    first appearance."""
    consolidated = []
    index_by_code = {}
    for line in stock_order.lines:
        code = (line.item_code or '').strip()
        if code and code in index_by_code:
            row = consolidated[index_by_code[code]]
            row['qty'] += (line.qty or 0.0)
            note = (line.notes or '').strip()
            if note and note not in row['_notes']:
                row['_notes'].append(note)
            if not row['description'] and line.description:
                row['description'] = line.description
        else:
            note = (line.notes or '').strip()
            row = {
                'item_code': line.item_code,
                'description': line.description,
                'qty': (line.qty or 0.0),
                '_notes': [note] if note else [],
            }
            consolidated.append(row)
            if code:
                index_by_code[code] = len(consolidated) - 1
    for row in consolidated:
        row['notes'] = '; '.join(row['_notes'])
        del row['_notes']
    return consolidated
```

`print_order()` passes it to the template as `print_lines`:

```python
return render_template('stock_orders/print.html', stock_order=stock_order,
                       so=so, print_lines=_consolidate_print_lines(stock_order))
```

The status-flip-on-first-print logic in `print_order()` is unchanged.

### 2. Template — `templates/stock_orders/print.html`

- Loop `print_lines` instead of `stock_order.lines` (rows use dict keys —
  Jinja `line.item_code` resolves dict items fine).
- Footer "Total Items" count changes from `stock_order.lines|length` to
  `print_lines|length` (now = number of distinct printed rows).

### 3. Tests — `tests/test_stock_orders.py`

Add cases against `GET /stock-orders/<id>/print`:

- **Merges duplicates:** two lines with the same `item_code` (qty 2 + 3)
  render as a single row with qty `5.00`; response contains one occurrence of
  that item code in the items table.
- **Distinct items untouched:** two different item codes still render two rows.
- **Blank codes stay separate:** two lines with empty `item_code` render as
  two rows, not merged.
- **Notes joined:** merged group with notes "A" and "B" shows both; duplicate
  identical notes are not repeated.

## Out of scope

- No DB/line changes, no migration (models untouched).
- Works Order / Picking List print (`works_orders/*_print.html`) — this spec
  is the STO print only. Flag as a follow-up if the same consolidation is
  wanted there.
- The on-screen STO detail view keeps showing individual lines (needed for
  per-line picking).

## Files touched

1. `routes/stock_orders.py` — add helper, pass context (1 handler line).
2. `templates/stock_orders/print.html` — loop + footer.
3. `tests/test_stock_orders.py` — 4 test cases.
