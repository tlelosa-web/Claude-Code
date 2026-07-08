from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import nullslast
from models import db, StockOrder, StockOrderLine, SalesOrder
from routes.sales_orders import can_close_sales_order
from services.order_filters import STO_ACTIVE

stock_orders_bp = Blueprint('stock_orders', __name__)

@stock_orders_bp.route('/stock-orders')
def list_orders():
    """List all Stock Orders."""
    view = request.args.get('view', 'all')
    query = (StockOrder.query
             .join(SalesOrder, StockOrder.so_id == SalesOrder.id, isouter=True))
    if view == 'open':
        query = query.filter(StockOrder.status.in_(STO_ACTIVE))
    orders = query.order_by(nullslast(SalesOrder.delivery_date.asc())).all()
    return render_template('stock_orders/list.html', orders=orders, view=view)

@stock_orders_bp.route('/stock-orders/<int:order_id>')
def view_order(order_id):
    """View Stock Order details."""
    stock_order = StockOrder.query.get_or_404(order_id)
    return render_template('stock_orders/detail.html', stock_order=stock_order)

@stock_orders_bp.route('/stock-orders/<int:order_id>/print')
def print_order(order_id):
    """Render print-friendly Stock Order document."""
    stock_order = StockOrder.query.get_or_404(order_id)
    so = stock_order.sales_order
    return render_template('stock_orders/print.html', stock_order=stock_order, so=so)

@stock_orders_bp.route('/stock-orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel a Stock Order."""
    stock_order = StockOrder.query.get_or_404(order_id)
    
    # Guard: cannot cancel if already complete
    if stock_order.status == 'Complete':
        flash("Cannot cancel a completed Stock Order.", "error")
        return redirect(url_for('stock_orders.view_order', order_id=order_id))
    
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
        items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
        item_payload = [item_to_bom_json(item) for item in items]
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
