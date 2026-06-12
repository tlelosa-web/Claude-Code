from flask import Blueprint, render_template, redirect, url_for, flash
from models import db, StockOrder, StockOrderLine

stock_orders_bp = Blueprint('stock_orders', __name__)

@stock_orders_bp.route('/stock-orders')
def list_orders():
    """List all Stock Orders."""
    orders = StockOrder.query.order_by(StockOrder.created_at.desc()).all()
    return render_template('stock_orders/list.html', orders=orders)

@stock_orders_bp.route('/stock-orders/<int:order_id>')
def view_order(order_id):
    """View Stock Order details."""
    stock_order = StockOrder.query.get_or_404(order_id)
    return render_template('stock_orders/detail.html', stock_order=stock_order)

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
