from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import nullslast
from models import db, StockOrder, StockOrderLine, SalesOrder, Item
from routes.sales_orders import can_close_sales_order
from services.order_filters import STO_ACTIVE
from services.stock_service import issue, reverse_issue

stock_orders_bp = Blueprint('stock_orders', __name__)


def _line_needs_pick(line):
    """True if this line still has outstanding qty AND that qty is actually
    pickable (its item_code resolves to a catalogue Item). A line whose
    item_code never matches the catalogue can never be picked via /pick, so
    it must not permanently block Complete — same tolerance complete_order()
    has always had for unmatched item codes."""
    outstanding = (line.qty or 0.0) - (line.qty_issued or 0.0)
    if outstanding <= 0:
        return False
    return Item.query.filter_by(code=line.item_code).first() is not None


def can_complete_stock_order(stock_order):
    return not any(_line_needs_pick(line) for line in stock_order.lines)

@stock_orders_bp.route('/stock-orders')
def list_orders():
    """List all Stock Orders."""
    view = request.args.get('view', 'open')
    query = (StockOrder.query
             .join(SalesOrder, StockOrder.so_id == SalesOrder.id, isouter=True))
    if view == 'open':
        query = query.filter(StockOrder.status.in_(STO_ACTIVE))
    elif view == 'closed':
        query = query.filter(~StockOrder.status.in_(STO_ACTIVE))
    orders = query.order_by(nullslast(SalesOrder.delivery_date.asc())).all()
    return render_template('stock_orders/list.html', orders=orders, view=view)

def _line_extras(stock_order):
    """Per-line Comments column + item link. comment: availability if the
    outstanding qty is covered, otherwise a shortfall referencing the
    closest-due open PO for that item. item_id: the matched catalogue
    Item's id (None if the line's item_code has no catalogue match), used
    by the template to link the Item Code cell to /items/<id>. Reuses
    item_to_bom_json()/services/demand.py for the available_qty arithmetic
    rather than re-deriving it inline — this calc is duplicated at several
    sites already (see
    .claude/agent-memory/reviewer/pattern_shortfall_duplication.md); adding
    a 6th independent copy here was avoided on purpose."""
    from routes.sales_orders import item_to_bom_json
    from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk, get_next_po_due_bulk

    items_by_code = {}
    for line in stock_order.lines:
        if line.item_code not in items_by_code:
            items_by_code[line.item_code] = Item.query.filter_by(code=line.item_code).first()

    item_ids = [item.id for item in items_by_code.values() if item]
    qty_on_order_map = get_qty_on_order_bulk(item_ids=item_ids)
    qty_committed_map = get_qty_committed_bulk(item_ids=item_ids, exclude_sto_id=stock_order.id)
    next_po_due_map = get_next_po_due_bulk(item_ids=item_ids)

    extras = {}
    for line in stock_order.lines:
        item = items_by_code.get(line.item_code)
        if not item:
            extras[line.id] = {'comment': 'Item not in catalogue', 'item_id': None}
            continue

        payload = item_to_bom_json(
            item,
            qty_on_order=qty_on_order_map.get(item.id, 0.0),
            qty_committed=qty_committed_map.get(item.id, 0.0),
        )
        available_qty = payload['available_qty']
        outstanding = (line.qty or 0.0) - (line.qty_issued or 0.0)

        if available_qty >= outstanding:
            comment = f'Available ({available_qty:.1f})'
        else:
            short = outstanding - available_qty
            due = next_po_due_map.get(item.id)
            if due:
                comment = f'Short {short:.1f} — on order, due {due.strftime("%d/%m/%Y")}'
            else:
                comment = f'Short {short:.1f} — not on order'

        extras[line.id] = {'comment': comment, 'item_id': item.id}

    return extras


@stock_orders_bp.route('/stock-orders/<int:order_id>')
def view_order(order_id):
    """View Stock Order details."""
    stock_order = StockOrder.query.get_or_404(order_id)
    return render_template('stock_orders/detail.html', stock_order=stock_order,
                           can_complete=can_complete_stock_order(stock_order),
                           line_extras=_line_extras(stock_order))

@stock_orders_bp.route('/stock-orders/<int:order_id>/print')
def print_order(order_id):
    """Render print-friendly Stock Order document."""
    stock_order = StockOrder.query.get_or_404(order_id)
    so = stock_order.sales_order
    return render_template('stock_orders/print.html', stock_order=stock_order, so=so)

@stock_orders_bp.route('/stock-orders/<int:order_id>/pick', methods=['POST'])
def pick_lines(order_id):
    """Confirm picks on individual Stock Order lines, deducting stock immediately per line."""
    stock_order = StockOrder.query.get_or_404(order_id)

    if stock_order.status not in ('Open', 'Picking'):
        flash(f"Cannot pick lines on a {stock_order.status} Stock Order.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    try:
        picked_by = request.form.get('picked_by', 'System').strip() or 'System'
        unmatched = []
        any_picked = False

        for line in stock_order.lines:
            raw_qty = request.form.get(f'pick_qty_{line.id}', '0')
            try:
                entered_qty = float(raw_qty)
            except (TypeError, ValueError):
                entered_qty = 0.0

            outstanding = (line.qty or 0.0) - (line.qty_issued or 0.0)
            clamped_qty = max(0, min(entered_qty, outstanding))

            if clamped_qty == 0:
                continue

            item = Item.query.filter_by(code=line.item_code).first()
            if not item:
                unmatched.append(line.item_code or '(blank)')
                continue

            issue(
                item_id=item.id,
                qty=clamped_qty,
                reference=stock_order.stock_order_number,
                notes=f"Picked for {stock_order.stock_order_number}",
                created_by=picked_by
            )
            line.qty_issued = (line.qty_issued or 0.0) + clamped_qty
            any_picked = True

        if unmatched:
            flash(
                f"No catalogue match for item code(s) {', '.join(unmatched)} — "
                "stock was not deducted for those lines.",
                "warning"
            )

        if not any_picked:
            flash("No pick quantities were entered.", "warning")
            return redirect(url_for('stock_orders.view_order', order_id=order_id))

        if stock_order.status == 'Open':
            stock_order.status = 'Picking'

        db.session.commit()
        flash(f"Picks confirmed for Stock Order {stock_order.stock_order_number}.", "success")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error confirming picks: {str(e)}", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

@stock_orders_bp.route('/stock-orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel a Stock Order."""
    stock_order = StockOrder.query.get_or_404(order_id)
    
    # Guard: cannot cancel if already complete
    if stock_order.status == 'Complete':
        flash("Cannot cancel a completed Stock Order.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    cancelled_by = request.form.get('cancelled_by', 'System').strip() or 'System'
    unmatched = []
    for line in stock_order.lines:
        if not line.qty_issued:
            continue
        item = Item.query.filter_by(code=line.item_code).first()
        if not item:
            unmatched.append(line.item_code or '(blank)')
            continue
        reverse_issue(
            item_id=item.id,
            qty=line.qty_issued,
            reference=stock_order.stock_order_number,
            notes=f"Reversed on cancel of {stock_order.stock_order_number}",
            created_by=cancelled_by
        )
        line.qty_issued = 0.0

    if unmatched:
        flash(
            f"No catalogue match for item code(s) {', '.join(unmatched)} — "
            "stock was not reversed for those lines.",
            "warning"
        )

    stock_order.status = 'Cancelled'
    db.session.commit()
    
    flash(f"Stock Order {stock_order.stock_order_number} has been cancelled.", "success")
    return redirect(url_for('stock_orders.view_order', order_id=order_id))

@stock_orders_bp.route('/stock-orders/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    """Mark a Stock Order as Complete."""
    stock_order = StockOrder.query.get_or_404(order_id)

    if stock_order.status == 'Cancelled':
        flash("Cannot complete a cancelled Stock Order.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    if stock_order.status == 'Complete':
        flash(f"Stock Order {stock_order.stock_order_number} is already complete.", "warning")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    if not can_complete_stock_order(stock_order):
        flash("All lines must be picked before this Stock Order can be completed.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    completed_by = request.form.get('completed_by', 'System').strip() or 'System'
    unmatched = []
    for line in stock_order.lines:
        qty_to_issue = (line.qty or 0.0) - (line.qty_issued or 0.0)
        if qty_to_issue <= 0:
            continue
        item = Item.query.filter_by(code=line.item_code).first()
        if not item:
            unmatched.append(line.item_code or '(blank)')
            continue
        issue(
            item_id=item.id,
            qty=qty_to_issue,
            reference=stock_order.stock_order_number,
            notes=f"Issued for {stock_order.stock_order_number}",
            created_by=completed_by
        )
        line.qty_issued = line.qty

    if unmatched:
        flash(
            f"No catalogue match for item code(s) {', '.join(unmatched)} — "
            "stock was not deducted for those lines.",
            "warning"
        )

    stock_order.status = 'Complete'
    db.session.flush()

    # Check if the Sales Order can be closed — all WOs and STOs must be Complete/Cancelled
    so = stock_order.sales_order
    if so:
        can_close, _ = can_close_sales_order(so.id)
        if can_close:
            so.status = 'Closed'
            db.session.flush()

    db.session.commit()

    flash(f"Stock Order {stock_order.stock_order_number} marked as Complete.", "success")
    return redirect(url_for('stock_orders.view_order', order_id=order_id))


@stock_orders_bp.route('/stock-orders/<int:order_id>/reopen', methods=['POST'])
def reopen_order(order_id):
    """Reopen a Complete or Cancelled Stock Order, reversing any issued stock."""
    stock_order = StockOrder.query.get_or_404(order_id)

    if stock_order.status not in ('Complete', 'Cancelled'):
        flash(
            f"Stock Order {stock_order.stock_order_number} is not Complete or Cancelled — nothing to reopen.",
            "error"
        )
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    reopened_by = request.form.get('reopened_by', 'System').strip() or 'System'
    unmatched = []

    if stock_order.status == 'Complete':
        for line in stock_order.lines:
            if not line.qty_issued:
                continue
            item = Item.query.filter_by(code=line.item_code).first()
            if not item:
                unmatched.append(line.item_code or '(blank)')
                continue
            reverse_issue(
                item_id=item.id,
                qty=line.qty_issued,
                reference=stock_order.stock_order_number,
                notes=f"Reversed on reopen of {stock_order.stock_order_number}",
                created_by=reopened_by
            )
            line.qty_issued = 0.0

    if unmatched:
        flash(
            f"No catalogue match for item code(s) {', '.join(unmatched)} — "
            "stock was not reversed for those lines.",
            "warning"
        )

    stock_order.status = 'Open'
    db.session.flush()

    # Cascade: if the parent SO was auto-closed because this STO completed, reopen it too.
    if stock_order.sales_order and stock_order.sales_order.status == 'Closed':
        stock_order.sales_order.status = 'Open'
        db.session.flush()

    db.session.commit()
    flash(f"Stock Order {stock_order.stock_order_number} has been reopened.", "success")
    return redirect(url_for('stock_orders.view_order', order_id=order_id))


@stock_orders_bp.route('/stock-orders/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    """Edit line items on an Open Stock Order."""
    import json
    from flask import request
    stock_order = StockOrder.query.get_or_404(order_id)

    if stock_order.status != 'Open':
        flash(f"Cannot edit a {stock_order.status} Stock Order.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    if request.method == 'GET':
        from models import Item
        from routes.sales_orders import item_to_bom_json
        from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk, get_next_po_due_bulk
        items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
        item_ids = [item.id for item in items]
        qty_on_order_map = get_qty_on_order_bulk(item_ids=item_ids)
        qty_committed_map = get_qty_committed_bulk(item_ids=item_ids, exclude_sto_id=order_id)
        next_po_due_map = get_next_po_due_bulk(item_ids=item_ids)
        item_payload = [
            item_to_bom_json(
                item,
                qty_on_order=qty_on_order_map.get(item.id, 0.0),
                qty_committed=qty_committed_map.get(item.id, 0.0),
                next_po_due=next_po_due_map.get(item.id),
            )
            for item in items
        ]
        categories = db.session.query(Item.category).filter(
            Item.active == True, Item.category != None
        ).distinct().order_by(Item.category).all()
        categories = [c[0] for c in categories if c[0]]
        return render_template('stock_orders/edit.html',
                               stock_order=stock_order,
                               items=item_payload,
                               categories=categories)

    # POST — replace all lines
    try:
        lines_json = request.form.get('lines_json', '[]')
        lines_data = json.loads(lines_json)

        StockOrderLine.query.filter_by(stock_order_id=stock_order.id).delete()
        db.session.flush()

        for ld in lines_data:
            qty = ld.get('qty', 0)
            try:
                qty = float(qty)
            except (TypeError, ValueError):
                qty = 0.0
            line = StockOrderLine(
                stock_order_id=stock_order.id,
                item_code=str(ld.get('item_code', '')).strip(),
                description=str(ld.get('description', '')).strip(),
                qty=qty,
                notes=str(ld.get('notes', '')).strip()
            )
            db.session.add(line)

        db.session.commit()
        flash(f"Stock Order {stock_order.stock_order_number} updated successfully.", "success")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating Stock Order: {str(e)}", "error")
        return redirect(url_for('stock_orders.edit_order', order_id=order_id))
